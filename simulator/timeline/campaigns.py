"""
NEXUS Simulator — Crime Campaign Manager
Organizes sequential crimes by the same gang into logical campaigns.
"""
from __future__ import annotations
import numpy as np
import logging
from datetime import date, timedelta
from typing import List, Dict, Optional, Any

from simulator.schemas.crimes import CrimeCampaign
from simulator.criminals.profiles import CriminalProfile
from simulator.timeline.calendar import DayContext
from simulator.geography.karnataka import Station

logger = logging.getLogger(__name__)

class CampaignManager:
    def __init__(self, rng: np.random.Generator):
        self.rng = rng
        self.active_campaigns: List[CrimeCampaign] = []
        self.completed_campaigns: List[CrimeCampaign] = []
        self._campaign_counter = 0

    def tick(
        self,
        current_date: date,
        active_criminals: List[CriminalProfile],
        stations: List[Station]
    ) -> List[CrimeCampaign]:
        """
        Advance active campaigns, complete finished ones, and start new ones.
        Returns the list of campaigns that should execute crimes today.
        """
        executing_today: List[CrimeCampaign] = []

        # 1. Start new campaigns
        # Only active criminals who are in gangs can start campaigns
        gang_leaders = [c for c in active_criminals if c.is_gang_leader and c.gang_id]
        if gang_leaders and self.rng.random() < 0.1:  # 10% chance per day to start a new campaign
            leader = self.rng.choice(gang_leaders)
            target_station = self.rng.choice(stations)
            
            # Decide campaign properties
            num_crimes = int(self.rng.integers(5, 25))
            duration_days = int(self.rng.integers(7, 30))
            crime_category = self.rng.choice(leader.preferred_crime_types) if leader.preferred_crime_types else "THEFT"
            
            self._campaign_counter += 1
            new_camp = CrimeCampaign(
                campaign_id=f"CAMP-{self._campaign_counter:04d}",
                gang_id=leader.gang_id,
                crime_category=crime_category,
                start_date=current_date,
                end_date=current_date + timedelta(days=duration_days),
                num_crimes_planned=num_crimes,
                num_crimes_committed=0,
                status="active",
                target_district_id=target_station.district_id
            )
            self.active_campaigns.append(new_camp)

        # 2. Advance existing campaigns
        still_active = []
        for camp in self.active_campaigns:
            if current_date > camp.end_date or camp.num_crimes_committed >= camp.num_crimes_planned:
                camp.status = "completed"
                self.completed_campaigns.append(camp)
            else:
                still_active.append(camp)
                
                # Should this campaign execute a crime today?
                # Distribute remaining crimes over remaining days
                days_left = (camp.end_date - current_date).days + 1
                crimes_left = camp.num_crimes_planned - camp.num_crimes_committed
                prob_today = crimes_left / max(1, days_left)
                
                if self.rng.random() < prob_today:
                    executing_today.append(camp)

        self.active_campaigns = still_active
        return executing_today
