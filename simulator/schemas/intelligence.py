from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class FinancialTransaction:
    transaction_id: str
    sender_id: str      # criminal_id or 'fence'
    receiver_id: str    # criminal_id or 'fence'
    amount_inr: float
    timestamp: datetime
    transaction_type: str # CASH, UPI, HAWALA, CRYPTO
    linked_campaign_id: Optional[str]
    notes: str

@dataclass
class IntelligenceTip:
    tip_id: str
    source_type: str    # INFORMANTS, INTERCEPT, ANONYMOUS
    timestamp: datetime
    district_id: str
    station_id: str
    target_criminal_id: Optional[str]
    target_gang_id: Optional[str]
    linked_campaign_id: Optional[str]
    confidence_score: float # 0.0 to 1.0
    description: str

@dataclass
class Mastermind:
    mastermind_id: str
    citizen_id: str
    name_en: str
    alias: str
    wealth_level: str
    controlled_gang_ids: List[str]
    front_business: str

@dataclass
class Informant:
    informant_id: str
    citizen_id: Optional[str]
    primary_station_id: str
    true_reliability_score: float # 0.1 to 0.95
    category: str # PETTY_CRIMINAL, SHOPKEEPER, RIVAL_GANG_MEMBER
    status: str # ACTIVE, COMPROMISED, RETIRED
