"""
NEXUS Simulator — Criminal Career State Machine
Manages state transitions for each criminal over simulation time:
  active → arrested → bail/acquitted → active (recidivism)
  active → retired
  juvenile → emerging → active → experienced → notorious
"""
from __future__ import annotations
import random
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Optional, Dict
from enum import Enum

from simulator.criminals.profiles import CriminalProfile


class CareerState(Enum):
    ACTIVE = "active"
    ARRESTED = "arrested"
    BAIL = "bail"
    CONVICTED = "convicted"
    RETIRED = "retired"
    ABSCONDING = "absconding"
    DECEASED = "deceased"


@dataclass
class CareerEvent:
    """A single career lifecycle event for a criminal."""
    criminal_id: str
    event_date: date
    event_type: str         # "arrested" | "bail_granted" | "convicted" | "retired" | "active"
    fir_id: Optional[str]
    station_id: Optional[str]
    notes: str


class CareerManager:
    """
    Manages criminal career states across simulation time.
    Updated per simulation tick.
    """

    def __init__(self, criminals: List[CriminalProfile], rng: random.Random) -> None:
        self.rng = rng
        self._states: Dict[str, CareerState] = {}
        self._events: Dict[str, List[CareerEvent]] = {}
        self._bail_dates: Dict[str, Optional[date]] = {}
        self._next_eligible: Dict[str, Optional[date]] = {}  # next date criminal is eligible to offend

        for c in criminals:
            if c.is_currently_arrested:
                self._states[c.criminal_id] = CareerState.ARRESTED
            elif c.career_stage == "retired":
                self._states[c.criminal_id] = CareerState.RETIRED
            else:
                self._states[c.criminal_id] = CareerState.ACTIVE
            self._events[c.criminal_id] = []
            self._bail_dates[c.criminal_id] = None
            self._next_eligible[c.criminal_id] = None

    def is_active(self, criminal_id: str) -> bool:
        return self._states.get(criminal_id, CareerState.ACTIVE) == CareerState.ACTIVE

    def get_state(self, criminal_id: str) -> CareerState:
        return self._states.get(criminal_id, CareerState.ACTIVE)

    def arrest(
        self,
        criminal: CriminalProfile,
        arrest_date: date,
        fir_id: str,
        station_id: str,
    ) -> None:
        """Mark a criminal as arrested."""
        self._states[criminal.criminal_id] = CareerState.ARRESTED
        criminal.is_currently_arrested = True
        criminal.is_currently_active = False
        criminal.total_arrests += 1

        # Estimate bail date (7–90 days later)
        days_to_bail = self.rng.randint(7, 90)
        bail_date = arrest_date + timedelta(days=days_to_bail)
        self._bail_dates[criminal.criminal_id] = bail_date

        self._events[criminal.criminal_id].append(CareerEvent(
            criminal_id=criminal.criminal_id,
            event_date=arrest_date,
            event_type="arrested",
            fir_id=fir_id,
            station_id=station_id,
            notes=f"Arrested in connection with FIR {fir_id}",
        ))

    def tick(self, current_date: date, criminals: List[CriminalProfile]) -> None:
        """
        Advance criminal career states for the current simulation date.
        - Criminals on bail may return to active
        - Some criminals may retire
        - Absconders may resurface
        """
        for criminal in criminals:
            cid = criminal.criminal_id
            state = self._states.get(cid, CareerState.ACTIVE)

            if state == CareerState.ARRESTED:
                bail_date = self._bail_dates.get(cid)
                if bail_date and current_date >= bail_date:
                    # Check recidivism
                    if self.rng.random() < criminal.recidivism_probability:
                        self._states[cid] = CareerState.ACTIVE
                        criminal.is_currently_active = True
                        criminal.is_currently_arrested = False
                        # Cooling off period after bail before next crime
                        cooling_days = self.rng.randint(14, 60)
                        self._next_eligible[cid] = current_date + timedelta(days=cooling_days)
                        self._events[cid].append(CareerEvent(
                            criminal_id=cid,
                            event_date=current_date,
                            event_type="bail_granted",
                            fir_id=None,
                            station_id=None,
                            notes="Released on bail. Recidivism likely.",
                        ))
                    else:
                        self._states[cid] = CareerState.CONVICTED
                        criminal.is_currently_active = False
                        criminal.career_stage = "retired"

            elif state == CareerState.ACTIVE:
                # Small chance of retiring voluntarily
                if criminal.age > 55 and self.rng.random() < 0.001:
                    self._states[cid] = CareerState.RETIRED
                    criminal.is_currently_active = False
                    criminal.career_stage = "retired"
                # Small chance of absconding (flees jurisdiction)
                elif criminal.risk_level == "very_high" and self.rng.random() < 0.0005:
                    self._states[cid] = CareerState.ABSCONDING

    def can_offend_today(self, criminal_id: str, current_date: date) -> bool:
        """Check if criminal is eligible to commit a crime today."""
        if not self.is_active(criminal_id):
            return False
        eligible_date = self._next_eligible.get(criminal_id)
        if eligible_date and current_date < eligible_date:
            return False
        return True

    def set_next_eligible(self, criminal_id: str, next_date: date) -> None:
        """Set the next date a criminal can offend (cooling-off period)."""
        self._next_eligible[criminal_id] = next_date

    def get_all_events(self) -> List[CareerEvent]:
        """Return all career events across all criminals."""
        events = []
        for event_list in self._events.values():
            events.extend(event_list)
        return sorted(events, key=lambda e: e.event_date)
