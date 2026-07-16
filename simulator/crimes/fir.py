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
import numpy as np
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
from simulator.schemas.crimes import Victim, Accused, FIR


FIR_STATUS_WEIGHTS = {
    "Under Investigation": 40,
    "Charge Sheet Filed":  25,
    "Final Report":        15,
    "Closed (Undetected)": 12,
    "Transferred":         5,
    "Withdrawn":           3,
}








def _build_description(
    crime_type: str,
    mo,
    loss: float,
    rng: np.random.Generator,
    use_kannada: bool = False,
) -> str:
    """Build a narrative FIR description with extreme diversity (styles, OCR noise, Kanglish)."""
    templates = FIR_DESC_TEMPLATES_KN if use_kannada else FIR_DESC_TEMPLATES_EN

    # 1. Base template selection
    ct = crime_type if crime_type in templates else "THEFT"
    pool = templates.get(ct, ["{crime_type} incident reported at {location}."])
    template = rng.choice(pool)

    # 2. Variable substitutions
    substitutions = {
        "{item}": rng.choice(["gold jewellery", "cash", "mobile phone", "laptop", "two-wheeler", "duddu", "bangaara"]),
        "{amount}": f"{int(loss):,}",
        "{location}": rng.choice(["complainant house", "market area", "street", "shop", "bus stand", "near railway gate", "mane hatra"]),
        "{date}": rng.choice(["the above date", "yesterday", "on the date of incident", "said date"]),
        "{time}": f"{int(rng.integers(19, 23 + 1)):02d}:00 hours",
        "{time1}": f"{int(rng.integers(8, 12 + 1)):02d}:00 hrs",
        "{time2}": f"{int(rng.integers(13, 18 + 1)):02d}:00 hrs",
        "{entry_method}": (mo.entry_method.replace("_", " ") if mo else "unknown means"),
        "{ipc}": "457",
        "{num}": str(mo.num_offenders if mo else 2),
        "{weapon}": (mo.weapon.replace("_", " ") if mo else "unknown weapon"),
        "{vehicle}": (mo.escape_vehicle.replace("_", " ") if mo else "motorcycle"),
        "{vehicle_type}": rng.choice(["motorcycle", "car", "auto rickshaw", "gadi", "bike"]),
        "{vehicle_reg}": f"KA {int(rng.integers(1, 50 + 1)):02d} {rng.choice(['AA','AB','BB','CC'])} {int(rng.integers(1000, 9999 + 1))}",
        "{weight}": str(int(rng.integers(5, 30 + 1))),
        "{drug_type}": rng.choice(["ganja", "heroin", "brown sugar", "drugs"]),
        "{pretext}": rng.choice(["investment scheme", "job offer", "government scheme", "lottery"]),
        "{reason}": rng.choice(["old enmity", "property dispute", "road rage", "galati"]),
        "{relation}": rng.choice(["neighbour", "relative", "acquaintance", "friend"]),
    }

    desc = template
    for k, v in substitutions.items():
        desc = desc.replace(k, str(v))

    # 3. Style variations (Formal, Colloquial, Abbreviated)
    if not use_kannada:
        style_roll = rng.random()
        if style_roll < 0.3:
            # Formal police style
            prefixes = ["It is submitted that ", "The complainant has approached the PS stating that ", "As per the written complaint received, "]
            desc = rng.choice(prefixes) + desc + rng.choice([" Requesting further investigation.", " FIR registered.", " Forwarded for necessary action."])
        elif style_roll < 0.6:
            # Abbreviated/Sloppy style
            desc = desc.replace("complainant", "complnt").replace("accused", "accsd").replace("house", "hs")
            desc = desc.replace("motorcycle", "MC").replace("vehicle", "veh")
            desc = desc.replace("investigation", "invst").replace("station", "PS")
            desc = "Info rcvd: " + desc
        
        # Kanglish/Hinglish mixing
        if rng.random() < 0.4:
            kanglish_map = {
                "stole": "kaddidare", "stolen": "kaddidare", "money": "duddu",
                "house": "mane", "vehicle": "gadi", "friend": "dost",
                "beat": "hoddedu", "threatened": "bedarike haakidare",
                "night": "ratri", "morning": "belagge"
            }
            for eng, kan in kanglish_map.items():
                if rng.random() < 0.3:
                    desc = desc.replace(eng, kan)

        # Spelling/OCR noise (simulating bad data entry)
        if rng.random() < 0.5:
            mistakes = {"the ": "teh ", "and ": "adn ", "from ": "form ", "reported": "reportd", "unknown": "unkown"}
            for correct, wrong in mistakes.items():
                if rng.random() < 0.3:
                    desc = desc.replace(correct, wrong)

    return desc


def _pick_fir_status(rng: np.random.Generator, reported_date: date) -> str:
    """Older FIRs are more likely to be resolved."""
    days_old = (date.today() - reported_date).days
    if days_old < 30:
        return "Under Investigation"
    statuses = list(FIR_STATUS_WEIGHTS.keys())
    weights = list(FIR_STATUS_WEIGHTS.values())
    weights_array = np.array(weights) / sum(weights)
    return rng.choice(statuses, p=weights_array)


def _make_victim(
    fir_id: str,
    idx: int,
    rng: np.random.Generator,
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
        age=int(rng.integers(18, 75 + 1)),
        phone=id_factory.phone(),
        address=f"No. {int(rng.integers(1, 200 + 1))}, {rng.choice(['Main Road','Cross','Layout'])}, Karnataka",
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
    rng: np.random.Generator,
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
    rng: np.random.Generator,
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
        delay_days = rng.choice([0, 1, 2, 3, 5], p=[0.50, 0.25, 0.12, 0.08, 0.05])
        reported_date = event.occurred_date + timedelta(days=int(delay_days))

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
            nearest_poi_id=event.nearest_poi_id,
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
            complainant_address=f"Karnataka - {int(rng.integers(560000, 597000 + 1))}",
            estimated_loss_inr=event.estimated_loss_inr,
            num_accused=len(accused_list),
            num_victims=len(victims),
            num_witnesses=len(event.witness_citizen_ids),
            gang_id=event.gang_id,
            campaign_id=event.campaign_id,
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