"""
NEXUS Simulator — Intelligence Events Generator
Generates Financial Transactions (Economy) and Intelligence Tips.
"""
from __future__ import annotations
import numpy as np
from datetime import datetime, timedelta
from typing import List, Tuple

from simulator.schemas.crimes import CrimeCampaign
from simulator.schemas.intelligence import FinancialTransaction, IntelligenceTip, Informant
from simulator.criminals.profiles import CriminalProfile
from simulator.geography.karnataka import Station

def generate_informants(
    rng: np.random.Generator,
    stations: List[Station],
    count: int = 50
) -> List[Informant]:
    informants = []
    categories = ["PETTY_CRIMINAL", "SHOPKEEPER", "RIVAL_GANG_MEMBER", "COMMUNITY_LEADER"]
    
    for i in range(count):
        station = rng.choice(stations)
        # Bimodal reliability: some are very reliable, most are mediocre
        if rng.random() < 0.2:
            true_rel = rng.uniform(0.7, 0.95)
        else:
            true_rel = rng.uniform(0.1, 0.6)
            
        informants.append(Informant(
            informant_id=f"INF-{i:04d}",
            citizen_id=None, # Anonymous
            primary_station_id=station.station_id,
            true_reliability_score=round(true_rel, 2),
            category=rng.choice(categories),
            status="ACTIVE"
        ))
    return informants

def generate_intelligence_events(
    campaigns: List[CrimeCampaign],
    criminals: List[CriminalProfile],
    stations: List[Station],
    informants: List[Informant],
    rng: np.random.Generator
) -> Tuple[List[FinancialTransaction], List[IntelligenceTip]]:
    transactions: List[FinancialTransaction] = []
    tips: List[IntelligenceTip] = []
    
    tx_counter = 0
    tip_counter = 0
    
    gang_leaders = [c for c in criminals if c.is_gang_leader]

    for camp in campaigns:
        leader = next((c for c in gang_leaders if c.gang_id == camp.gang_id), None)
        if not leader:
            continue
            
        camp_dt = datetime.combine(camp.start_date, datetime.min.time())
        
        # 1. Financial Transactions (selling stolen goods to fence -> fence paying leader)
        if camp.crime_category in ["THEFT", "BURGLARY", "ROBBERY", "DACOITY", "VEH_THEFT"]:
            # Stolen property sold to fence
            amount = float(rng.integers(10000, 500000))
            fence_id = f"FENCE-{rng.integers(1, 100):03d}"
            
            tx_dt = camp_dt + timedelta(days=int(rng.integers(1, 10)))
            transactions.append(FinancialTransaction(
                transaction_id=f"TX-{tx_counter:08d}",
                sender_id=fence_id,
                receiver_id=leader.criminal_id,
                amount_inr=amount,
                timestamp=tx_dt,
                transaction_type=rng.choice(["CASH", "UPI", "HAWALA"]),
                linked_campaign_id=camp.campaign_id,
                notes="Proceeds from stolen property sale"
            ))
            tx_counter += 1
            
            # Leader distributing cut to accomplice
            if leader.known_associates:
                acc_id = rng.choice(leader.known_associates)
                cut = amount * rng.uniform(0.1, 0.4)
                tx_dt_2 = tx_dt + timedelta(days=1)
                transactions.append(FinancialTransaction(
                    transaction_id=f"TX-{tx_counter:08d}",
                    sender_id=leader.criminal_id,
                    receiver_id=acc_id,
                    amount_inr=round(cut, 2),
                    timestamp=tx_dt_2,
                    transaction_type=rng.choice(["UPI", "CASH"]),
                    linked_campaign_id=camp.campaign_id,
                    notes="Distribution of campaign proceeds"
                ))
                tx_counter += 1
                
        # 2. Intelligence Tips (intercepts about campaign)
        if rng.random() < 0.4:  # 40% chance of tip being generated for a campaign
            tip_dt = camp_dt - timedelta(days=int(rng.integers(1, 5))) # Tip before campaign starts
            station = rng.choice(stations)
            
            source_type = rng.choice(["INFORMANT", "INTERCEPT", "ANONYMOUS"])
            conf = round(rng.uniform(0.3, 0.9), 2)
            
            if source_type == "INFORMANT" and informants:
                inf = rng.choice(informants)
                # Confidence score is true reliability + noise
                noise = rng.uniform(-0.1, 0.1)
                conf = round(max(0.0, min(1.0, inf.true_reliability_score + noise)), 2)
            
            tips.append(IntelligenceTip(
                tip_id=f"TIP-{tip_counter:08d}",
                source_type=source_type,
                timestamp=tip_dt,
                district_id=camp.target_district_id,
                station_id=station.station_id,
                target_criminal_id=leader.criminal_id,
                target_gang_id=camp.gang_id,
                linked_campaign_id=camp.campaign_id,
                confidence_score=conf,
                description=f"Information regarding planned {camp.crime_category} activities in the area."
            ))
            tip_counter += 1

    return transactions, tips
