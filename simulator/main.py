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
import random
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

    rng = random.Random(settings.seed)
    logger.info(f"[*] NEXUS Simulator | Scale: {scale} | Seed: {seed} | Target FIRs: {settings.fir_count:,}")

    # ── Phase 1: Geography ────────────────────────────────────────────────
    logger.info("Phase 1/11: Building Karnataka geography...")
    from simulator.geography.karnataka import build_geography
    from simulator.geography.locations import generate_locations
    from simulator.geography.coordinates import CoordinateSampler

    districts, stations = build_geography(rng)
    locations = generate_locations(stations, rng, max_locations_per_station=20)
    coord_sampler = CoordinateSampler(stations, rng)
    logger.info(f"  >> {len(districts)} districts | {len(stations)} stations | {len(locations)} locations")

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

    criminals = generate_criminal_profiles(citizens, settings.criminal_fraction, rng)
    logger.info(f"  >> {len(criminals):,} criminal profiles")

    # ── Phase 4: Gangs ────────────────────────────────────────────────────
    logger.info("Phase 4/11: Forming gangs...")
    from simulator.criminals.gangs import generate_gangs
    from simulator.criminals.career import CareerManager

    gangs = generate_gangs(criminals, settings.gang_count, rng, settings.sim_start_year)
    career_manager = CareerManager(criminals, rng)
    criminals_map = {c.criminal_id: c for c in criminals}
    logger.info(f"  >> {len(gangs)} gangs | Career manager initialized")

    # ── Phase 5: Timeline + Crime Events ─────────────────────────────────
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
    engine.register_crime_generator(generate_crime_events)
    engine.run(target_fir_count=settings.fir_count)

    crime_events = engine.raw_crime_events
    sim_dates = [dc.date for dc in engine.simulation_days]
    logger.info(f"  >> {len(crime_events):,} crime events generated over {len(sim_dates)} days")

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

    logger.info(
        f"  >> {len(evidence):,} evidence | {len(arrests):,} arrests | "
        f"{len(chargesheets):,} chargesheets | {len(patrol_logs):,} patrols | "
        f"{len(cctv_events):,} CCTV events"
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

    logger.info(f"[DONE] NEXUS simulation complete. Output: {settings.output_dir.resolve()}")
    return sim_data
