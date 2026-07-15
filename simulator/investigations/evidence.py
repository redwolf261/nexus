"""
NEXUS Simulator — Evidence Generator
Generates evidence records per FIR with:
  - Evidence type, description, collection date
  - Chain of custody (officer → lab → court)
  - Forensic report stubs
  - CCTV clip references
  - Recovery status
"""
from __future__ import annotations
import random
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Optional, Dict

from simulator.config.constants import EVIDENCE_TYPES
from simulator.crimes.fir import FIR


@dataclass
class ChainOfCustodyEntry:
    handler_id: str       # officer_id or lab_id
    handler_type: str     # "officer" | "forensic_lab" | "court"
    received_date: date
    action: str           # "collected" | "analyzed" | "submitted" | "produced_in_court"
    notes: str


@dataclass
class Evidence:
    evidence_id: str
    fir_id: str
    evidence_type: str
    description: str
    collection_date: date
    collection_officer_id: Optional[str]
    collection_location: str
    condition: str          # "good" | "damaged" | "partial" | "contaminated"
    is_forensic: bool
    forensic_report_id: Optional[str]
    lab_name: Optional[str]
    lab_received_date: Optional[date]
    lab_result: Optional[str]
    is_recovered_property: bool
    estimated_value_inr: float
    chain_of_custody: List[ChainOfCustodyEntry] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)  # searchable tags


FORENSIC_LABS = [
    "KFSL Bengaluru", "KFSL Mysuru", "KFSL Hubballi",
    "Regional Forensic Lab Mangaluru", "District Forensic Lab",
]

EVIDENCE_DESCRIPTIONS = {
    "physical_object": [
        "Seized iron rod used as weapon",
        "Recovered stolen gold jewellery",
        "Stolen mobile phone recovered from accused",
        "Country-made weapon seized",
        "Stolen two-wheeler recovered",
        "Broken window glass collected from scene",
    ],
    "cctv_footage": [
        "CCTV footage from nearby bank ATM showing accused",
        "Shop CCTV footage showing accused vehicle",
        "Traffic camera footage of escape route",
        "Hotel CCTV showing accused check-in",
        "Market CCTV footage retrieved",
    ],
    "witness_statement": [
        "Statement of eye witness recorded under Sec 161 CrPC",
        "Voluntary statement of witness given",
        "Statement of shop keeper recorded",
        "Statement of auto driver who saw accused",
        "Neighbour's statement recorded",
    ],
    "forensic_report": [
        "Fingerprint report from KFSL",
        "DNA analysis report",
        "Ballistic report on firearm",
        "Chemical analysis of seized narcotic",
        "Tool mark examination report",
        "Blood group analysis report",
    ],
    "call_records": [
        "CDR of accused mobile obtained from service provider",
        "WhatsApp call records obtained",
        "Tower location data obtained for accused phone",
        "Call records linking accused to other suspects",
    ],
    "bank_records": [
        "Bank account statement of accused showing proceeds",
        "UPI transaction records showing fund transfer",
        "ATM withdrawal records from crime location",
        "Hawala transaction records",
    ],
    "fingerprints": [
        "Fingerprints lifted from crime scene matched with accused",
        "Palm print lifted from window sill",
        "Latent fingerprints developed using powder technique",
    ],
    "dna_sample": [
        "Blood sample collected from crime scene",
        "Hair sample collected from crime scene",
        "Saliva sample from cigarette butt",
    ],
    "digital_evidence": [
        "Mobile phone seized containing incriminating photos",
        "Laptop seized with fraud-related files",
        "SIM card seized",
        "Memory card with crime-related content",
    ],
    "confession": [
        "Voluntary confession statement of accused",
        "Disclosure statement u/s 27 Evidence Act",
    ],
    "recovered_property": [
        "Stolen cash recovered from accused",
        "Stolen jewellery identified and recovered",
        "Recovered vehicle from accused's possession",
    ],
    "vehicle_tracking": [
        "GPS tracker data from accused vehicle",
        "FASTag records showing vehicle movement",
        "Toll plaza records with vehicle photograph",
    ],
}

CRIME_EVIDENCE_MAP: Dict[str, List[str]] = {
    "THEFT":     ["physical_object", "cctv_footage", "witness_statement", "fingerprints"],
    "BURGLARY":  ["fingerprints", "cctv_footage", "physical_object", "witness_statement", "forensic_report"],
    "ROBBERY":   ["witness_statement", "cctv_footage", "physical_object", "recovered_property"],
    "DACOITY":   ["witness_statement", "forensic_report", "recovered_property", "call_records"],
    "CHAIN":     ["cctv_footage", "witness_statement", "vehicle_tracking"],
    "VEH_THEFT": ["cctv_footage", "vehicle_tracking", "recovered_property"],
    "FRAUD":     ["bank_records", "call_records", "digital_evidence", "witness_statement"],
    "CYBER":     ["digital_evidence", "call_records", "bank_records"],
    "ATM_FRAUD": ["cctv_footage", "digital_evidence", "bank_records"],
    "ASSAULT":   ["forensic_report", "witness_statement", "physical_object", "dna_sample"],
    "MURDER":    ["forensic_report", "dna_sample", "fingerprints", "witness_statement", "call_records"],
    "NARCOTICS": ["physical_object", "forensic_report", "call_records", "bank_records"],
    "KIDNAP":    ["call_records", "cctv_footage", "witness_statement", "vehicle_tracking"],
    "DEFAULT":   ["physical_object", "witness_statement", "cctv_footage"],
}


def generate_evidence(
    firs: List[FIR],
    officers_by_station: Dict[str, list],
    rng: random.Random,
) -> List[Evidence]:
    """Generate 1–6 evidence records per FIR."""
    all_evidence: List[Evidence] = []
    evidence_counter = 0

    for fir in firs:
        evidence_types_for_crime = CRIME_EVIDENCE_MAP.get(fir.crime_type, CRIME_EVIDENCE_MAP["DEFAULT"])
        num_evidence = rng.randint(1, min(6, len(evidence_types_for_crime)))
        selected_types = rng.sample(evidence_types_for_crime, min(num_evidence, len(evidence_types_for_crime)))

        for etype in selected_types:
            collection_delay = rng.randint(0, 7)
            collection_date = fir.reported_date + timedelta(days=collection_delay)

            # Collecting officer
            station_offs = officers_by_station.get(fir.station_id, [])
            coll_officer_id = rng.choice(station_offs).officer_id if station_offs else None

            is_forensic = etype in {"forensic_report", "dna_sample", "fingerprints", "ballistic"}
            lab_name = rng.choice(FORENSIC_LABS) if is_forensic else None
            lab_received = collection_date + timedelta(days=rng.randint(1, 14)) if is_forensic else None
            lab_result = None
            if is_forensic and lab_received:
                result_options = [
                    "Matches with accused sample",
                    "Positive for narcotics",
                    "No match found",
                    "Inconclusive",
                    "Fingerprint matched with accused",
                    "DNA matches accused profile",
                ]
                lab_result = rng.choice(result_options)

            descriptions = EVIDENCE_DESCRIPTIONS.get(etype, ["Evidence collected"])
            description = rng.choice(descriptions)

            forensic_report_id = f"FSL-{evidence_counter:07d}" if is_forensic else None
            is_recovered = etype == "recovered_property"
            value = fir.estimated_loss_inr * rng.uniform(0.3, 1.0) if is_recovered else 0.0

            # Chain of custody
            custody_chain: List[ChainOfCustodyEntry] = [
                ChainOfCustodyEntry(
                    handler_id=coll_officer_id or "OFF-UNKNOWN",
                    handler_type="officer",
                    received_date=collection_date,
                    action="collected",
                    notes=f"Collected from crime scene at {fir.latitude},{fir.longitude}",
                )
            ]
            if is_forensic and lab_received:
                custody_chain.append(ChainOfCustodyEntry(
                    handler_id=lab_name or "KFSL",
                    handler_type="forensic_lab",
                    received_date=lab_received,
                    action="analyzed",
                    notes=f"Sent to {lab_name} for analysis",
                ))

            tags = [etype, fir.crime_type, fir.crime_category]
            if is_recovered:
                tags.append("recovered_property")

            all_evidence.append(Evidence(
                evidence_id=f"EVI-{evidence_counter:08d}",
                fir_id=fir.fir_id,
                evidence_type=etype,
                description=description,
                collection_date=collection_date,
                collection_officer_id=coll_officer_id,
                collection_location=f"Crime scene near lat:{fir.latitude}, lng:{fir.longitude}",
                condition=rng.choices(["good", "damaged", "partial", "contaminated"], weights=[60, 15, 20, 5], k=1)[0],
                is_forensic=is_forensic,
                forensic_report_id=forensic_report_id,
                lab_name=lab_name,
                lab_received_date=lab_received,
                lab_result=lab_result,
                is_recovered_property=is_recovered,
                estimated_value_inr=round(value, 2),
                chain_of_custody=custody_chain,
                tags=tags,
            ))
            evidence_counter += 1

    return all_evidence
