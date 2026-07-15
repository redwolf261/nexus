"""
NEXUS Simulator — Noise Injector
Applies realistic data quality imperfections to the generated datasets:
  - Missing values (random field nulling)
  - OCR character errors in text fields
  - GPS coordinate jitter
  - Duplicate FIR records (clerical errors)
  - Date format inconsistencies
  - Spelling variants in names
  - Partial addresses
  - Alias substitution in FIR descriptions
Every noisy record maintains a link back to the clean canonical record.
"""
from __future__ import annotations
import numpy as np
import copy
from dataclasses import asdict
from datetime import date
from typing import List, Dict, Any, Tuple

from simulator.crimes.fir import FIR
from simulator.criminals.profiles import CriminalProfile
from simulator.noise.aliases import AliasGenerator


DATE_FORMATS = ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d.%m.%Y", "%d %b %Y"]

# Field-level missing probability (fraction of records where field is nulled)
MISSING_VALUE_PROBABILITY: Dict[str, float] = {
    "description_kn": 0.45,       # Kannada description often missing
    "complainant_phone": 0.08,
    "estimated_loss_inr": 0.12,
    "investigating_officer_id": 0.10,
    "gang_id": 0.0,                # Never null — structural field
    "festival_context": 0.0,
    "gang_id": 0.0,
}

OCR_CHARS = {
    "0": "O", "O": "0", "1": "l", "l": "1",
    "5": "S", "S": "5", "2": "Z", "Z": "2",
    "8": "B", "B": "8",
}


class NoiseInjector:
    """
    Applies configurable data quality noise to simulation outputs.
    Maintains a noise_map for traceability.
    """

    def __init__(self, rng: np.random.Generator, noise_fraction: float = 0.15) -> None:
        self.rng = rng
        self.noise_fraction = noise_fraction
        self.alias_gen = AliasGenerator(rng)
        self.noise_map: Dict[str, str] = {}  # noisy_id → canonical_id

    def inject_fir_noise(self, firs: List[FIR]) -> Tuple[List[FIR], List[FIR]]:
        """
        Inject noise into a fraction of FIR records.
        Returns (clean_firs, noisy_firs).
        Noisy FIRs are separate records pointing back to canonical via noise_map.
        """
        noisy_firs: List[FIR] = []
        for fir in firs:
            if self.rng.random() > self.noise_fraction:
                continue

            # Pick a noise type
            noise_type = self.rng.choice([
                "missing_fields", "ocr_error", "gps_jitter", "missing_gps",
                "date_format", "duplicate", "alias_name", "inconsistent_address"
            ])

            noisy_fir = self._clone_fir(fir)
            noisy_fir_id = f"{fir.fir_id}-NOISE"
            self.noise_map[noisy_fir_id] = fir.fir_id

            if noise_type == "missing_fields":
                self._apply_missing_fields(noisy_fir)
                if noisy_fir.phone_ids and self.rng.random() < 0.5:
                    noisy_fir.phone_ids = []  # drop linked phones
            elif noise_type == "ocr_error":
                noisy_fir.complainant_name = self._ocr_corrupt_text(fir.complainant_name)
                noisy_fir.description_en = self._ocr_corrupt_text(fir.description_en[:100])
            elif noise_type == "gps_jitter":
                noisy_fir.latitude  = round(fir.latitude  + self.rng.uniform(-0.01, 0.01), 6)
                noisy_fir.longitude = round(fir.longitude + self.rng.uniform(-0.01, 0.01), 6)
            elif noise_type == "missing_gps":
                noisy_fir.latitude = None
                noisy_fir.longitude = None
            elif noise_type == "date_format":
                # Date stored as alternative string representation (handled in export)
                pass
            elif noise_type == "duplicate":
                # Duplicate FIR (same crime, two registrations — clerical error)
                noisy_fir.fir_number = fir.fir_number + "/DUP"
            elif noise_type == "alias_name":
                aliases = self.alias_gen.generate_aliases(fir.complainant_name, "", num_aliases=1)
                if aliases:
                    noisy_fir.complainant_name = aliases[0]
            elif noise_type == "inconsistent_address":
                addr = fir.complainant_address
                addr = addr.replace("Road", "Rd").replace("Street", "St").replace("Cross", "Crs")
                if self.rng.random() < 0.5:
                    addr = addr[:-7] # Drop pincode e.g. " - 560001"
                noisy_fir.complainant_address = addr

            noisy_firs.append(noisy_fir)

        return firs, noisy_firs

    def inject_criminal_name_noise(
        self,
        criminals: List[CriminalProfile],
    ) -> Dict[str, List[str]]:
        """
        Generate name aliases for criminals.
        Returns: {criminal_id: [alias1, alias2, ...]}
        """
        alias_map: Dict[str, List[str]] = {}
        for criminal in criminals:
            num_aliases = int(self.rng.integers(1, 3 + 1))
            aliases = self.alias_gen.generate_aliases(
                criminal.name_en, criminal.name_kn, num_aliases
            )
            if aliases:
                alias_map[criminal.criminal_id] = aliases
                criminal.alias_names = aliases
        return alias_map

    def _clone_fir(self, fir: FIR) -> FIR:
        """Shallow clone of FIR for noise application."""
        return FIR(
            fir_id=fir.fir_id + "-NOISE",
            fir_number=fir.fir_number,
            station_id=fir.station_id,
            district_id=fir.district_id,
            district_name=fir.district_name,
            occurred_date=fir.occurred_date,
            reported_date=fir.reported_date,
            crime_type=fir.crime_type,
            crime_category=fir.crime_category,
            ipc_sections=list(fir.ipc_sections),
            severity=fir.severity,
            status=fir.status,
            description_en=fir.description_en,
            description_kn=fir.description_kn,
            latitude=fir.latitude,
            longitude=fir.longitude,
            investigating_officer_id=fir.investigating_officer_id,
            sho_officer_id=fir.sho_officer_id,
            complainant_name=fir.complainant_name,
            complainant_phone=fir.complainant_phone,
            complainant_address=fir.complainant_address,
            estimated_loss_inr=fir.estimated_loss_inr,
            num_accused=fir.num_accused,
            num_victims=fir.num_victims,
            num_witnesses=fir.num_witnesses,
            gang_id=fir.gang_id,
            is_gang_crime=fir.is_gang_crime,
            festival_context=fir.festival_context,
            season=fir.season,
            primary_criminal_id=fir.primary_criminal_id,
            accomplice_criminal_ids=list(fir.accomplice_criminal_ids),
            vehicle_ids=list(fir.vehicle_ids),
            phone_ids=list(fir.phone_ids),
            event_id=fir.event_id,
            victims=[],
            accused_list=[],
        )

    def _apply_missing_fields(self, fir: FIR) -> None:
        """Randomly null out some optional fields."""
        for field_name, prob in MISSING_VALUE_PROBABILITY.items():
            if hasattr(fir, field_name) and self.rng.random() < prob:
                setattr(fir, field_name, None)

    def _ocr_corrupt_text(self, text: str) -> str:
        """Apply OCR-style character confusions to a text string."""
        chars = list(text)
        for i, ch in enumerate(chars):
            if ch in OCR_CHARS and self.rng.random() < 0.05:
                chars[i] = OCR_CHARS[ch]
        return "".join(chars)
