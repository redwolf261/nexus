"""
NEXUS Simulator — Main Orchestrator
Runs all simulation phases in order:
  1. Config
  2. Geography
  3. Population
  4. Criminal Profiles
  5. Gangs
  6. Timeline + Crime Events
  7. FIR Assembly
  8. Investigations
  9. Graph Building
 10. Noise Injection
 11. Validation
 12. Export
"""
from __future__ import annotations
import logging
import numpy as np
import sys
from datetime import date
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger("nexus.simulator")

# ─────────────────────────────────────────────────────────────────────────────
# Internal simulator init (ensures simulator package is on path)
# ─────────────────────────────────────────────────────────────────────────────
def _setup_path():
    root = Path(__file__).resolve().parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

_setup_path()


def run_simulation(
    scale: str = "medium",
    seed: int = 42,
    output_dir: str = "output",
    export_csv: bool = True,
    export_json: bool = True,
    export_neo4j: bool = True,
    export_geojson: bool = True,
    export_parquet: bool = False,
    enable_noise: bool = True,
    validate: bool = True,
) -> Dict[str, Any]:
    """
    Run the full NEXUS crime world simulation.
    Returns a dict with all generated data objects.
    """
    from simulator.config.settings import Settings
    from simulator.config.constants import Constants

    settings = Settings(
        seed=seed,
        scale=scale,
        output_dir=Path(output_dir),
        neo4j_dir=Path(output_dir) / "neo4j",
        geojson_dir=Path(output_dir) / "geojson",
        export_csv=export_csv,
        export_json=export_json,
        export_neo4j=export_neo4j,
        export_geojson=export_geojson,
        export_parquet=export_parquet,
        enable_noise=enable_noise,
    )

    rng = np.random.default_rng(settings.seed)
    logger.info(f"[*] NEXUS Simulator | Scale: {scale} | Seed: {seed} | Target FIRs: {settings.fir_count:,}")

    # ── Phase 1: Geography ────────────────────────────────────────────────
    logger.info("Phase 1/11: Building Karnataka geography...")
    from simulator.geography.karnataka import build_geography
    from simulator.geography.locations import generate_locations
    from simulator.geography.coordinates import CoordinateSampler

    from simulator.geography.pois import generate_pois

    districts, stations = build_geography(rng)
    locations = generate_locations(stations, rng, max_locations_per_station=20)
    pois = generate_pois(stations, rng)
    
    logger.info("  >> Initializing GIS Engine (Roads & Spatial Index)...")
    from simulator.gis.roads import RoadNetworkManager
    from simulator.gis.spatial_index import GISPrecomputation
    
    district_ids = [d.district_id for d in districts]
    road_manager = RoadNetworkManager(district_ids, rng)
    gis_index = GISPrecomputation()
    gis_index.load_stations(stations)
    gis_index.load_pois(pois)
    
    from simulator.investigations.sensors import build_sensor_networks
    towers, cctv_cams, anpr_cams = build_sensor_networks(stations, rng)
    
    coord_sampler = CoordinateSampler(stations, rng)
    logger.info(f"  >> {len(districts)} districts | {len(stations)} stations | {len(locations)} locations | {len(pois)} POIs")
    logger.info(f"  >> {len(towers)} Cell Towers | {len(cctv_cams)} CCTV Cameras | {len(anpr_cams)} ANPR Cameras")

    # ── Phase 2: Population ───────────────────────────────────────────────
    logger.info("Phase 2/11: Generating population...")
    from simulator.population.identifiers import IdentifierFactory
    from simulator.population.citizens import generate_citizens
    from simulator.population.officers import generate_officers

    id_factory = IdentifierFactory(rng)
    citizens = generate_citizens(settings.citizen_count, stations, id_factory, rng)
    officers = generate_officers(stations, id_factory, rng, settings.officer_multiplier)
    logger.info(f"  >> {len(citizens):,} citizens | {len(officers):,} officers")

    # Officers by station index
    officers_by_station: Dict[str, list] = {}
    for o in officers:
        officers_by_station.setdefault(o.station_id, []).append(o)

    # ── Phase 3: Criminal Profiles ────────────────────────────────────────
    logger.info("Phase 3/11: Building criminal profiles...")
    from simulator.criminals.profiles import generate_criminal_profiles
    from simulator.population.devices import generate_devices

    criminals = generate_criminal_profiles(citizens, settings.criminal_fraction, rng)
    
    vehicles, phones = generate_devices(citizens, criminals, rng, settings.sim_start_year)
    vehicles_by_criminal = {c.criminal_id: c.vehicle_ids for c in criminals}
    phones_by_criminal = {c.criminal_id: c.phone_ids for c in criminals}
    
    logger.info(f"  >> {len(criminals):,} criminal profiles | {len(vehicles):,} vehicles | {len(phones):,} phones")

    # ── Phase 3.5: Social Networks & Masterminds ──────────────────────────
    logger.info("Phase 3.5/11: Generating Social Networks & Masterminds...")
    from simulator.population.relationships import generate_social_ties
    from simulator.criminals.mastermind import generate_masterminds
    
    social_ties = generate_social_ties(citizens, criminals, rng, settings.sim_start_year)
    logger.info(f"  >> {len(social_ties):,} social ties")

    # ── Phase 4: Gangs ────────────────────────────────────────────────────
    logger.info("Phase 4/11: Forming gangs...")
    from simulator.criminals.gangs import generate_gangs
    from simulator.criminals.career import CareerManager
    from simulator.criminals.mastermind import generate_masterminds

    gangs = generate_gangs(criminals, settings.gang_count, rng, settings.sim_start_year)
    career_manager = CareerManager(criminals, rng)
    criminals_map = {c.criminal_id: c for c in criminals}
    logger.info(f"  >> {len(gangs)} gangs formed | {sum(len(g.member_criminal_ids) for g in gangs)} gang members")
    
    masterminds = generate_masterminds(citizens, gangs, rng, count=5)
    logger.info(f"  >> {len(masterminds)} hidden masterminds overseeing gangs")

    # ── Phase 5: Timeline Simulation ────────────────────────────────────────
    logger.info("Phase 5/11: Running simulation timeline...")
    from simulator.timeline.engine import SimulationEngine
    from simulator.crimes.events import generate_crime_events

    engine = SimulationEngine(
        settings=settings,
        rng=rng,
        criminals=criminals,
        stations=stations,
        career_manager=career_manager,
        coord_sampler=coord_sampler,
    )
    from functools import partial
    engine.register_crime_generator(
        partial(generate_crime_events, vehicles_by_criminal=vehicles_by_criminal, phones_by_criminal=phones_by_criminal, pois=pois)
    )
    engine.run(target_fir_count=settings.fir_count)

    crime_events = engine.raw_crime_events
    sim_dates = [dc.date for dc in engine.simulation_days]
    campaigns = engine.campaign_manager.completed_campaigns + engine.campaign_manager.active_campaigns
    logger.info(f"  >> {len(crime_events):,} crime events generated over {len(sim_dates)} days | {len(campaigns)} campaigns")

    # ── Phase 6: FIR Assembly ─────────────────────────────────────────────
    logger.info("Phase 6/11: Assembling FIRs...")
    from simulator.crimes.fir import assemble_firs
    from simulator.crimes.modus_operandi import MoFingerprint

    firs, victims, accused = assemble_firs(
        crime_events=crime_events,
        criminals_map=criminals_map,
        officers_by_station=officers_by_station,
        id_factory=id_factory,
        rng=rng,
        enable_kannada=settings.enable_kannada,
    )

    # Collect MO fingerprints
    mo_fingerprints = [e.modus_operandi for e in crime_events if e.modus_operandi]

    logger.info(f"  >> {len(firs):,} FIRs | {len(victims):,} victims | {len(accused):,} accused")

    # ── Phase 7: Investigations ───────────────────────────────────────────
    logger.info("Phase 7/11: Generating investigations...")
    from simulator.investigations.evidence import generate_evidence
    from simulator.investigations.arrests import generate_arrests
    from simulator.investigations.patrol import generate_patrol_logs
    from simulator.investigations.cctv import generate_cctv_events

    evidence = generate_evidence(firs, officers_by_station, rng)
    arrests, chargesheets = generate_arrests(firs, officers_by_station, rng)

    patrol_logs = []
    if settings.enable_patrol_logs:
        patrol_logs = generate_patrol_logs(stations, officers, sim_dates, id_factory, rng)

    cctv_events = []
    if settings.enable_cctv:
        cctv_events = generate_cctv_events(firs, stations, id_factory, rng)
        
    from simulator.investigations.telecom import generate_telecom_data
    cdrs = generate_telecom_data(crime_events, criminals, citizens, rng)
    
    from simulator.investigations.sensors import generate_sensor_traces
    cell_pings, vehicle_gps, cctv_logs, anpr_logs = generate_sensor_traces(
        crime_events, towers, cctv_cams, anpr_cams, vehicles, rng
    )
    
    from simulator.investigations.court import generate_court_cases
    court_cases = generate_court_cases(chargesheets, rng)
    
    from simulator.investigations.lifecycle import generate_investigation_logs
    investigation_logs = generate_investigation_logs(firs, evidence, arrests, chargesheets, rng)
    
    from simulator.investigations.intelligence_events import generate_intelligence_events, generate_informants
    informants = generate_informants(rng, stations, count=100)
    financial_tx, intel_tips = generate_intelligence_events(campaigns, criminals, stations, informants, rng)

    logger.info(
        f"  >> {len(evidence):,} evidence | {len(arrests):,} arrests | "
        f"{len(chargesheets):,} chargesheets | {len(patrol_logs):,} patrols | "
        f"{len(cctv_events):,} CCTV events | {len(cdrs):,} CDRs | "
        f"{len(investigation_logs):,} investigation logs | {len(financial_tx):,} financial tx | "
        f"{len(intel_tips):,} intel tips"
    )
    logger.info(
        f"  >> {len(court_cases):,} court cases | {len(informants):,} informants | "
        f"{len(cell_pings):,} cell pings | {len(vehicle_gps):,} GPS pings | "
        f"{len(cctv_logs):,} CCTV logs | {len(anpr_logs):,} ANPR logs"
    )

    # ── Phase 8: Graph Building ───────────────────────────────────────────
    logger.info("Phase 8/11: Building knowledge graph...")
    from simulator.graph.builder import CrimeKnowledgeGraph
    from simulator.graph.neo4j_export import export_neo4j_csvs

    graph = CrimeKnowledgeGraph()
    graph.add_stations(stations)
    graph.add_officers(officers)
    graph.add_criminals(criminals)
    graph.add_gangs(gangs)
    graph.add_firs(firs, criminals_map)
    graph.add_evidence(evidence)
    graph.add_associate_edges(criminals)

    gstats = graph.stats()
    logger.info(f"  >> {gstats['num_nodes']:,} graph nodes | {gstats['num_edges']:,} graph edges")

    # ── Phase 9: Noise Injection ──────────────────────────────────────────
    noisy_firs = []
    alias_map: Dict[str, list] = {}
    from simulator.noise.ground_truth import EntityResolutionGroundTruth
    er_ground_truth = EntityResolutionGroundTruth()

    if settings.enable_noise:
        logger.info("Phase 9/11: Injecting noise...")
        from simulator.noise.injector import NoiseInjector

        noise_injector = NoiseInjector(rng, settings.noise_fraction)
        _, noisy_firs = noise_injector.inject_fir_noise(firs)
        alias_map = noise_injector.inject_criminal_name_noise(criminals)

        fir_map = {f.fir_id: f for f in firs}
        er_ground_truth.add_from_noise_map(noise_injector.noise_map, fir_map)
        for cid, aliases in alias_map.items():
            criminal = criminals_map.get(cid)
            if criminal:
                er_ground_truth.add_criminal_aliases(cid, criminal.name_en, aliases)

        logger.info(
            f"  >> {len(noisy_firs)} noisy FIRs | {len(alias_map)} criminals aliased | "
            f"{len(er_ground_truth)} ER records"
        )

    # ── Phase 10: Validation ──────────────────────────────────────────────
    if validate:
        logger.info("Phase 10/11: Validating simulation...")
        from simulator.validation.validator import SimulationValidator

        validator = SimulationValidator()
        val_result = validator.validate_all(
            stations=stations,
            officers=officers,
            criminals=criminals,
            firs=firs,
            arrests=arrests,
            evidence=evidence,
            graph=graph,
            road_manager=road_manager,
        )
        status = "[PASSED]" if val_result["passed"] else "[ISSUES FOUND]"
        logger.info(f"  Validation {status} | Errors: {val_result['total_errors']} | Warnings: {val_result['total_warnings']}")
        if not val_result["passed"]:
            logger.warning(validator.report())

    # ── Phase 11: Export ──────────────────────────────────────────────────
    logger.info("Phase 11/11: Exporting datasets...")

    sim_data = {
        "districts":        districts,
        "stations":         stations,
        "pois":             pois,
        "officers":         officers,
        "citizens":         citizens,
        "criminals":        criminals,
        "gangs":            gangs,
        "firs":             firs,
        "victims":          victims,
        "accused":          accused,
        "evidence":         evidence,
        "arrests":          arrests,
        "chargesheets":     chargesheets,
        "patrol_logs":      patrol_logs,
        "cctv_events":      cctv_events,
        "modus_operandi":   mo_fingerprints,
        "entity_resolution":er_ground_truth.to_records(),
        "noisy_firs":       noisy_firs,
        "vehicles":         vehicles,
        "phones":           phones,
        "cdrs":             cdrs,
        "campaigns":        campaigns,
        "investigation_logs": investigation_logs,
        "financial_transactions": financial_tx,
        "intelligence_tips": intel_tips,
        "social_ties":      social_ties,
        "masterminds":      masterminds,
        "court_cases":      court_cases,
        "informants":       informants,
        "cell_towers":      towers,
        "cctv_cameras":     cctv_cams,
        "anpr_cameras":     anpr_cams,
        "cell_pings":       cell_pings,
        "vehicle_gps":      vehicle_gps,
        "cctv_logs":        cctv_logs,
        "anpr_logs":        anpr_logs,
        "daily_context":    engine.simulation_days,
        "district_daily_summaries": getattr(engine, "district_daily_summaries", []),
        "road_manager":     road_manager,
    }

    if settings.export_csv:
        from simulator.export.csv_exporter import export_all_csv
        export_all_csv(sim_data, settings.output_dir)

    if settings.export_json:
        from simulator.export.json_exporter import export_json
        export_json(sim_data, settings.output_dir)

    if settings.export_neo4j:
        export_neo4j_csvs(graph, settings.neo4j_dir)

    if settings.export_geojson:
        from simulator.export.geojson_exporter import export_geojson
        export_geojson(sim_data, settings.geojson_dir)

    if settings.export_parquet:
        from simulator.export.parquet_exporter import export_parquet
        export_parquet(sim_data, settings.output_dir / "parquet")

    # ── Final Demo Outputs ────────────────────────────────────────────────
    from simulator.export.demo_packager import export_demo_pack
    export_demo_pack(sim_data, settings.output_dir)

    logger.info(f"[DONE] NEXUS simulation complete. Output: {settings.output_dir.resolve()}")
    return sim_data
