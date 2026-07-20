"""
NEXUS Ingestion — Dataset Catalogue

Single source of truth for how every simulator output maps into the data layer.
Drives the Postgres loader (load order, junction expansion), and documents which
datasets are graph-eligible vs Postgres-only.

Terminology:
  - table:        target Postgres table name
  - pk:           primary-key column(s) in the CSV
  - list_columns: pipe-delimited columns expanded into junction tables
  - store:        "both" (Postgres + graph subgraph) | "postgres" (relational only)
  - skip reason:  datasets intentionally not ingested (corrupt / non-relational)

Load order is topological (parents before children). The gangs<->criminals cycle
is resolved by loading criminals with gang_id nullable, then gangs, then backfilling.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass(frozen=True)
class Dataset:
    key: str                       # logical name
    csv: str                       # filename in output/
    table: Optional[str]           # target table (None if skipped)
    pk: Optional[str]              # primary key column
    store: str = "postgres"        # "both" | "postgres"
    list_columns: tuple = ()       # pipe-delimited columns (kept as text unless junction below)
    skip: bool = False
    skip_reason: str = ""


# ── Topological load order (index = phase) ──────────────────────────────────
# Parents must appear before children. Junction backfills run after their parents.
LOAD_ORDER: List[str] = [
    # Phase 1 — geography & infrastructure (no FKs)
    "districts",
    # Phase 2 — stations (FK district)
    "stations",
    # Phase 3 — officers + sensor infra + POIs (FK station/district)
    "officers", "pois", "cctv_cameras", "anpr_cameras", "cell_towers",
    # Phase 4 — population
    "persons",
    # Phase 5 — assets (FK persons)
    "vehicles", "phones",
    # Phase 6 — criminals (gang_id nullable to break cycle)
    "criminals",
    # Phase 7 — gangs (FK leader->criminals), then backfill criminals.gang_id
    "gangs",
    # Phase 8 — campaigns & masterminds
    "campaigns", "masterminds",
    # Phase 9 — FIRs (central fact; many FKs)
    "firs",
    # Phase 10 — case children (FK fir)
    "victims", "accused", "evidence", "investigation_logs", "modus_operandi",
    "chargesheets",
    # Phase 11 — depends on case children
    "arrests", "court_cases",
    # Phase 12 — telemetry (Postgres-only, soft refs)
    "cctv_logs", "cctv_events", "anpr_logs", "cdrs", "cell_tower_pings",
    "vehicle_gps", "patrol_logs",
    # Phase 13 — intelligence & misc (Postgres-only, soft/polymorphic refs)
    "financial_transactions", "intelligence_tips", "informants",
    "social_network", "entity_resolution",
]


# ── Dataset definitions ─────────────────────────────────────────────────────
DATASETS: Dict[str, Dataset] = {d.key: d for d in [
    # Geography / infra
    Dataset("districts", "districts.csv", "districts", "district_id", "both"),
    Dataset("stations", "stations.csv", "stations", "station_id", "both"),
    Dataset("officers", "officers.csv", "officers", "officer_id", "both"),
    Dataset("pois", "pois.csv", "pois", "poi_id", "postgres"),
    Dataset("cctv_cameras", "cctv_cameras.csv", "cctv_cameras", "camera_id", "postgres"),
    Dataset("anpr_cameras", "anpr_cameras.csv", "anpr_cameras", "anpr_id", "postgres"),
    Dataset("cell_towers", "cell_towers.csv", "cell_towers", "tower_id", "postgres"),

    # Population & assets
    Dataset("persons", "persons.csv", "persons", "citizen_id", "both"),
    Dataset("vehicles", "vehicles.csv", "vehicles", "vehicle_id", "both"),
    Dataset("phones", "phones.csv", "phones", "phone_id", "both"),

    # Criminal network (list cols -> junctions handled in pg_loader)
    Dataset("criminals", "criminals.csv", "criminals", "criminal_id", "both",
            list_columns=("known_associates",)),
    Dataset("gangs", "gangs.csv", "gangs", "gang_id", "both",
            list_columns=("member_criminal_ids",)),
    Dataset("campaigns", "ground_truth_campaigns.csv", "campaigns", "campaign_id", "both"),
    Dataset("masterminds", "ground_truth_masterminds.csv", "masterminds", "mastermind_id", "postgres"),

    # Central fact + case children
    Dataset("firs", "firs.csv", "firs", "fir_id", "both",
            list_columns=("accomplice_criminal_ids", "vehicle_ids", "phone_ids")),
    Dataset("victims", "victims.csv", "victims", "victim_id", "both"),
    Dataset("accused", "accused.csv", "accused", "accused_id", "postgres"),
    Dataset("evidence", "evidence.csv", "evidence", "evidence_id", "both"),
    Dataset("investigation_logs", "investigation_logs.csv", "investigation_logs", "log_id", "postgres"),
    Dataset("modus_operandi", "modus_operandi.csv", "modus_operandi", "crime_event_id", "postgres"),
    Dataset("chargesheets", "chargesheets.csv", "chargesheets", "chargesheet_id", "postgres"),
    Dataset("arrests", "arrests.csv", "arrests", "arrest_id", "postgres"),
    Dataset("court_cases", "court_cases.csv", "court_cases", "case_id", "postgres"),

    # Telemetry (Postgres-only)
    Dataset("cctv_logs", "cctv_logs.csv", "cctv_logs", "log_id", "postgres"),
    Dataset("cctv_events", "cctv_events.csv", "cctv_events", "cctv_event_id", "postgres"),
    Dataset("anpr_logs", "anpr_logs.csv", "anpr_logs", "log_id", "postgres"),
    Dataset("cdrs", "cdrs.csv", "cdrs", "cdr_id", "postgres"),
    Dataset("cell_tower_pings", "cell_tower_pings.csv", "cell_tower_pings", "ping_id", "postgres"),
    Dataset("vehicle_gps", "vehicle_gps.csv", "vehicle_gps", "gps_id", "postgres"),
    Dataset("patrol_logs", "patrol_logs.csv", "patrol_logs", "log_id", "postgres"),

    # Intelligence & misc (Postgres-only, soft/polymorphic refs)
    Dataset("financial_transactions", "financial_transactions.csv", "financial_transactions", "transaction_id", "postgres"),
    Dataset("intelligence_tips", "intelligence_tips.csv", "intelligence_tips", "tip_id", "postgres"),
    Dataset("informants", "informants.csv", "informants", "informant_id", "postgres"),
    Dataset("social_network", "social_network.csv", "social_network", None, "postgres"),
    Dataset("entity_resolution", "entity_resolution.csv", "entity_resolution", None, "postgres"),
]}


# ── Datasets intentionally NOT ingested ─────────────────────────────────────
SKIPPED: Dict[str, str] = {
    "daily_context.csv": "Corrupt export — Python object reprs (<DayContext object at 0x...>), not tabular data.",
    "firs_with_noise.csv": "Noise-augmented duplicate of firs.csv for ML robustness testing; not a distinct entity.",
    "crime_statistics.json": "Aggregate statistics, not relational.",
    "gang_network.json": "Denormalized aggregate of gangs.csv; relational form already loaded.",
    "simulation_summary.json": "Run metadata; used by validation for row-count parity, not a table.",
}


# ── Junction table specs (expanded from pipe-delimited list columns) ────────
@dataclass(frozen=True)
class Junction:
    table: str
    parent_key: str      # column in source CSV holding the parent id (the PK)
    list_column: str     # pipe-delimited column to explode
    left_col: str        # junction column for parent
    right_col: str       # junction column for each exploded value
    source_csv: str


JUNCTIONS: List[Junction] = [
    Junction("gang_members", "gang_id", "member_criminal_ids", "gang_id", "criminal_id", "gangs.csv"),
    Junction("criminal_associates", "criminal_id", "known_associates", "criminal_id", "associate_id", "criminals.csv"),
    Junction("fir_accomplices", "fir_id", "accomplice_criminal_ids", "fir_id", "criminal_id", "firs.csv"),
    Junction("fir_vehicles", "fir_id", "vehicle_ids", "fir_id", "vehicle_id", "firs.csv"),
    Junction("fir_phones", "fir_id", "phone_ids", "fir_id", "phone_id", "firs.csv"),
]


def datasets_in_load_order() -> List[Dataset]:
    return [DATASETS[k] for k in LOAD_ORDER if k in DATASETS]
