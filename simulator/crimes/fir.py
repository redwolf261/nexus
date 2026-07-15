"""
NEXUS Simulator — FIR Assembler
Converts raw CrimeEvents into full FIR records with:
  - FIR number (KA/DIST/YEAR/NNNNN format)
  - Complainant details
  - English and Kannada description
  - IPC sections
  - Station, date, status
  - Investigating officer
  - Victim/accused lists
"""
from __future__ import annotations
import random
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Optional, Dict

from simulator.config.constants import (
    FIR_DESC_TEMPLATES_EN, FIR_DESC_TEMPLATES_KN,
    EN_MALE_FIRST_NAMES, EN_FEMALE_FIRST_NAMES, EN_SURNAMES,
    MO_ESCAPE_VEHICLES,
)
from simulator.crimes.events import CrimeEvent
from simulator.criminals.profiles import CriminalProfile
from simulator.population.citizens import Citizen
from simulator.population.officers import Officer
from simulator.population.identifiers import IdentifierFactory


FIR_STATUS_WEIGHTS = {
    "Under Investigation": 40,
    "Charge Sheet Filed":  25,
    "Final Report":        15,
    "Closed (Undetected)": 12,
    "Transferred":         5,
    "Withdrawn":           3,
}


@dataclass
class Victim:
    victim_id: str
    fir_id: str
    name_en: str
    gender: str
    age: int
    phone: str
    address: str
    injury_type: str        # "none" | "minor" | "grievous" | "fatal"
    property_lost: str
    loss_amount_inr: float
    citizen_id: Optional[str]


@dataclass
class Accused:
    accused_id: str
    fir_id: str
    criminal_id: Optional[str]
    name_en: str
    name_kn: str
    age: Optional[int]
    gender: Optional[str]
    address: Optional[str]
    is_known: bool          # Known to police or named in FIR
    is_arrested: bool
    role: str               # "principal" | "accomplice" | "abettor"


@dataclass
class FIR:
    fir_id: str
    fir_number: str             # KA/DIST/YEAR/NNNNN
    station_id: str
    district_id: str
    district_name: str
    occurred_date: date
    reported_date: date         # May be 1-3 days after occurrence
    crime_type: str
    crime_category: str
    ipc_sections: List[str]
    severity: int
    status: str
    description_en: str
    description_kn: str
    latitude: float
    longitude: float
    investigating_officer_id: Optional[str]
    sho_officer_id: Optional[str]
    complainant_name: str
    complainant_phone: str
    complainant_address: str
    estimated_loss_inr: float
    num_accused: int
    num_victims: int
    num_witnesses: int
    gang_id: Optional[str]
    is_gang_crime: bool
    festival_context: Optional[str]
    season: str
    primary_criminal_id: Optional[str]
    accomplice_criminal_ids: List[str]
    vehicle_ids: List[str]
    phone_ids: List[str]
    event_id: str               # Link back to CrimeEvent
    victims: List[Victim] = field(default_factory=list)
    accused_list: List[Accused] = field(default_factory=list)


def _build_description(
    crime_type: str,
    mo,
    loss: float,
    rng: random.Random,
    use_kannada: bool = False,
) -> str:
    """Build a narrative FIR description from template."""
    templates = FIR_DESC_TEMPLATES_KN if use_kannada else FIR_DESC_TEMPLATES_EN

    # Fallback to English keys for Kannada if not found
    ct = crime_type if crime_type in templates else "THEFT"
    pool = templates.get(ct, ["{crime_type} incident reported at {location}."])
    template = rng.choice(pool)

    # Fill template placeholders
    substitutions = {
        "{item}": rng.choice(["gold jewellery", "cash", "mobile phone", "laptop", "two-wheeler"]),
        "{amount}": f"{int(loss):,}",
        "{location}": rng.choice(["the complainant's house", "market area", "street", "shop", "bus stand"]),
        "{date}": "the above date",
        "{time}": f"{rng.randint(19, 23):02d}:00 hours",
        "{time1}": f"{rng.randint(8, 12):02d}:00 hrs",
        "{time2}": f"{rng.randint(13, 18):02d}:00 hrs",
        "{entry_method}": (mo.entry_method.replace("_", " ") if mo else "unknown means"),
        "{ipc}": "457",
        "{num}": str(mo.num_offenders if mo else 2),
        "{weapon}": (mo.weapon.replace("_", " ") if mo else "unknown weapon"),
        "{vehicle}": (mo.escape_vehicle.replace("_", " ") if mo else "motorcycle"),
        "{vehicle_type}": rng.choice(["motorcycle", "car", "auto rickshaw"]),
        "{vehicle_reg}": f"KA {rng.randint(1,50):02d} {rng.choice(['AA','AB','BB','CC'])} {rng.randint(1000,9999)}",
        "{weight}": str(rng.randint(5, 30)),
        "{drug_type}": rng.choice(["ganja", "heroin", "brown sugar"]),
        "{pretext}": rng.choice(["investment scheme", "job offer", "government scheme", "lottery"]),
        "{reason}": rng.choice(["old enmity", "property dispute", "road rage"]),
        "{relation}": rng.choice(["neighbour", "relative", "acquaintance"]),
    }

    desc = template
    for k, v in substitutions.items():
        desc = desc.replace(k, str(v))

    return desc


def _pick_fir_status(rng: random.Random, reported_date: date) -> str:
    """Older FIRs are more likely to be resolved."""
    days_old = (date.today() - reported_date).days
    if days_old < 30:
        return "Under Investigation"
    statuses = list(FIR_STATUS_WEIGHTS.keys())
    weights = list(FIR_STATUS_WEIGHTS.values())
    return rng.choices(statuses, weights=weights, k=1)[0]


def _make_victim(
    fir_id: str,
    idx: int,
    rng: random.Random,
    id_factory: IdentifierFactory,
    loss: float,
    crime_type: str,
) -> Victim:
    gender = rng.choice(["M", "F"])
    first = rng.choice(EN_MALE_FIRST_NAMES if gender == "M" else EN_FEMALE_FIRST_NAMES)
    last = rng.choice(EN_SURNAMES)

    injury = "none"
    if crime_type in {"ASSAULT", "MURDER", "ATTEMPT_M", "ROBBERY", "DACOITY", "RIOTING"}:
        injury = rng.choice(["minor", "minor", "grievous", "fatal" if crime_type == "MURDER" else "grievous"])

    return Victim(
        victim_id=f"VIC-{fir_id}-{idx:03d}",
        fir_id=fir_id,
        name_en=f"{first} {last}",
        gender=gender,
        age=rng.randint(18, 75),
        phone=id_factory.phone(),
        address=f"No. {rng.randint(1,200)}, {rng.choice(['Main Road','Cross','Layout'])}, Karnataka",
        injury_type=injury,
        property_lost=rng.choice(["gold_jewellery", "cash", "mobile", "vehicle", "none"]),
        loss_amount_inr=loss / max(1, idx),
        citizen_id=None,
    )


def _make_accused(
    fir_id: str,
    idx: int,
    criminal: Optional[CriminalProfile],
    is_principal: bool,
    rng: random.Random,
) -> Accused:
    if criminal:
        return Accused(
            accused_id=f"ACC-{fir_id}-{idx:03d}",
            fir_id=fir_id,
            criminal_id=criminal.criminal_id,
            name_en=criminal.name_en,
            name_kn=criminal.name_kn,
            age=criminal.age,
            gender=criminal.gender,
            address=None,  # May be filled after noise injection
            is_known=rng.random() < 0.55,
            is_arrested=rng.random() < 0.25,
            role="principal" if is_principal else "accomplice",
        )
    else:
        gender = rng.choice(["M", "F", "M"])
        first = rng.choice(EN_MALE_FIRST_NAMES if gender == "M" else EN_FEMALE_FIRST_NAMES)
        return Accused(
            accused_id=f"ACC-{fir_id}-{idx:03d}",
            fir_id=fir_id,
            criminal_id=None,
            name_en=f"{first} {rng.choice(EN_SURNAMES)}",
            name_kn="ಅಜ್ಞಾತ",  # Unknown in Kannada
            age=None,
            gender=gender,
            address=None,
            is_known=False,
            is_arrested=False,
            role="principal" if is_principal else "accomplice",
        )


def assemble_firs(
    crime_events: List[CrimeEvent],
    criminals_map: Dict[str, CriminalProfile],
    officers_by_station: Dict[str, List[Officer]],
    id_factory: IdentifierFactory,
    rng: random.Random,
    enable_kannada: bool = True,
) -> tuple[List[FIR], List[Victim], List[Accused]]:
    """
    Convert raw crime events into FIR records with victims and accused lists.
    """
    all_firs: List[FIR] = []
    all_victims: List[Victim] = []
    all_accused: List[Accused] = []

    # FIR sequence counters per district per year
    fir_counters: Dict[str, int] = {}

    for event in crime_events:
        # FIR numbering
        year = event.occurred_date.year
        dist_code = event.district_id.replace("KA-", "").replace("-", "")
        key = f"{dist_code}-{year}"
        fir_counters[key] = fir_counters.get(key, 0) + 1
        seq = fir_counters[key]

        fir_id = f"FIR-{dist_code}-{year}-{seq:05d}"
        fir_number = id_factory.case_number(dist_code, year, seq)

        # Delay in reporting (0–5 days)
        delay_days = rng.choices([0, 1, 2, 3, 5], weights=[50, 25, 12, 8, 5], k=1)[0]
        reported_date = event.occurred_date + timedelta(days=delay_days)

        # Investigating officer
        io: Optional[Officer] = None
        sho: Optional[Officer] = None
        station_officers = officers_by_station.get(event.station_id, [])
        ios = [o for o in station_officers if o.is_investigating_officer]
        shos = [o for o in station_officers if o.is_station_house_officer]
        if ios:
            io = rng.choice(ios)
        if shos:
            sho = shos[0]

        # Complainant (separate from victim — often same person)
        c_gender = rng.choice(["M", "F"])
        c_first = rng.choice(EN_MALE_FIRST_NAMES if c_gender == "M" else EN_FEMALE_FIRST_NAMES)
        complainant_name = f"{c_first} {rng.choice(EN_SURNAMES)}"
        complainant_phone = id_factory.phone()

        # Descriptions
        desc_en = _build_description(event.crime_type, event.modus_operandi, event.estimated_loss_inr, rng, False)
        desc_kn = ""
        if enable_kannada and rng.random() < 0.60:
            desc_kn = _build_description(event.crime_type, event.modus_operandi, event.estimated_loss_inr, rng, True)

        status = _pick_fir_status(rng, reported_date)

        # Build IPC sections (primary + additional)
        ipc_sections = [event.ipc_section]
        if event.modus_operandi.is_violent and "324" not in ipc_sections:
            ipc_sections.append("324")
        if event.modus_operandi.weapon not in {"none", "bare_hands"} and "34" not in ipc_sections:
            ipc_sections.append("34")  # Common intention

        # Victims
        num_victims = len(event.victim_citizen_ids)
        victims = [
            _make_victim(fir_id, i, rng, id_factory, event.estimated_loss_inr, event.crime_type)
            for i in range(max(1, num_victims))
        ]

        # Accused
        accused_list = []
        primary_criminal = criminals_map.get(event.primary_criminal_id) if event.primary_criminal_id else None
        if primary_criminal:
            accused_list.append(_make_accused(fir_id, 0, primary_criminal, True, rng))
        else:
            accused_list.append(_make_accused(fir_id, 0, None, True, rng))

        for acc_idx, acc_cid in enumerate(event.accomplice_criminal_ids[:4], start=1):
            acc_criminal = criminals_map.get(acc_cid)
            accused_list.append(_make_accused(fir_id, acc_idx, acc_criminal, False, rng))

        all_victims.extend(victims)
        all_accused.extend(accused_list)

        # Update event
        event.fir_registered = True
        event.fir_id = fir_id

        all_firs.append(FIR(
            fir_id=fir_id,
            fir_number=fir_number,
            station_id=event.station_id,
            district_id=event.district_id,
            district_name=event.district_name,
            occurred_date=event.occurred_date,
            reported_date=reported_date,
            crime_type=event.crime_type,
            crime_category=event.crime_category,
            ipc_sections=ipc_sections,
            severity=event.severity,
            status=status,
            description_en=desc_en,
            description_kn=desc_kn,
            latitude=event.latitude,
            longitude=event.longitude,
            investigating_officer_id=io.officer_id if io else None,
            sho_officer_id=sho.officer_id if sho else None,
            complainant_name=complainant_name,
            complainant_phone=complainant_phone,
            complainant_address=f"Karnataka - {rng.randint(560000, 597000)}",
            estimated_loss_inr=event.estimated_loss_inr,
            num_accused=len(accused_list),
            num_victims=len(victims),
            num_witnesses=len(event.witness_citizen_ids),
            gang_id=event.gang_id,
            is_gang_crime=event.is_gang_crime,
            festival_context=event.festival_context,
            season=event.day_context,
            primary_criminal_id=event.primary_criminal_id,
            accomplice_criminal_ids=event.accomplice_criminal_ids,
            vehicle_ids=event.vehicle_ids_involved,
            phone_ids=event.phone_ids_involved,
            event_id=event.event_id,
            victims=victims,
            accused_list=accused_list,
        ))

    return all_firs, all_victims, all_accused
