"""
NEXUS Simulator — Global Settings
Changing SCALE is the only thing needed to switch between simulation sizes.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


# ─────────────────────────────────────────────
# MASTER SCALE KNOB
# Options: "small" | "medium" | "large" | "research"
# ─────────────────────────────────────────────
SCALE: Literal["small", "medium", "large", "research"] = "medium"

SCALE_PROFILES = {
    "small": {
        "fir_count": 1_000,
        "citizen_multiplier": 5,
        "criminal_fraction": 0.05,
        "gang_count": 5,
        "officer_multiplier": 0.3,
        "patrol_days": 30,
        "noise_fraction": 0.12,
    },
    "medium": {
        "fir_count": 25_000,
        "citizen_multiplier": 5,
        "criminal_fraction": 0.05,
        "gang_count": 25,
        "officer_multiplier": 0.3,
        "patrol_days": 365,
        "noise_fraction": 0.15,
    },
    "large": {
        "fir_count": 120_000,
        "citizen_multiplier": 5,
        "criminal_fraction": 0.06,
        "gang_count": 80,
        "officer_multiplier": 0.3,
        "patrol_days": 730,
        "noise_fraction": 0.15,
    },
    "research": {
        "fir_count": 1_000_000,
        "citizen_multiplier": 6,
        "criminal_fraction": 0.06,
        "gang_count": 300,
        "officer_multiplier": 0.3,
        "patrol_days": 1825,
        "noise_fraction": 0.18,
    },
}


@dataclass
class Settings:
    """Central configuration object for the NEXUS simulator."""

    # ── Reproducibility ───────────────────────────────────────────────────
    seed: int = 42

    # ── Scale ─────────────────────────────────────────────────────────────
    scale: str = SCALE

    # ── Output ────────────────────────────────────────────────────────────
    output_dir: Path = field(default_factory=lambda: Path("output"))
    neo4j_dir: Path = field(default_factory=lambda: Path("output/neo4j"))
    geojson_dir: Path = field(default_factory=lambda: Path("output/geojson"))

    # ── Export formats ────────────────────────────────────────────────────
    export_csv: bool = True
    export_json: bool = True
    export_neo4j: bool = True
    export_geojson: bool = True
    export_parquet: bool = False  # Enable for large/research scale

    # ── Feature flags ─────────────────────────────────────────────────────
    enable_noise: bool = True
    enable_kannada: bool = True
    enable_cctv: bool = True
    enable_patrol_logs: bool = True
    enable_parquet: bool = False

    # ── Simulation date range ─────────────────────────────────────────────
    sim_start_year: int = 2021
    sim_start_month: int = 1
    sim_start_day: int = 1

    def __post_init__(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.neo4j_dir.mkdir(parents=True, exist_ok=True)
        self.geojson_dir.mkdir(parents=True, exist_ok=True)

    @property
    def profile(self) -> dict:
        return SCALE_PROFILES[self.scale]

    @property
    def fir_count(self) -> int:
        return self.profile["fir_count"]

    @property
    def citizen_count(self) -> int:
        return self.fir_count * self.profile["citizen_multiplier"]

    @property
    def criminal_fraction(self) -> float:
        return self.profile["criminal_fraction"]

    @property
    def gang_count(self) -> int:
        return self.profile["gang_count"]

    @property
    def officer_multiplier(self) -> float:
        return self.profile["officer_multiplier"]

    @property
    def patrol_days(self) -> int:
        return self.profile["patrol_days"]

    @property
    def noise_fraction(self) -> float:
        return self.profile["noise_fraction"]


# Singleton — import this everywhere
settings = Settings()
