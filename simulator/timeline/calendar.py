"""
NEXUS Simulator — Karnataka Calendar
Provides per-day crime risk multipliers based on:
  - Weekday vs weekend
  - Festivals and public holidays
  - Seasons / monsoon
  - Tourism seasons
  - School holidays
Each day returns a dict of crime_type → risk_multiplier.
"""
from __future__ import annotations
from datetime import date, timedelta
from typing import Dict, List, Optional

from simulator.config.constants import FESTIVALS, CRIME_CATEGORIES


# Monthly baseline risk multipliers (seasonal effects)
# Monsoon (Jun–Sep) reduces street crime, winter festivals increase it
MONTHLY_BASELINE: Dict[int, float] = {
    1:  1.05,   # January — cool, Republic Day
    2:  0.95,   # February
    3:  1.10,   # March — Holi, Ugadi
    4:  1.00,
    5:  1.05,   # Summer heat — petty crime rises
    6:  0.85,   # Monsoon onset
    7:  0.80,   # Peak monsoon
    8:  0.82,
    9:  1.10,   # Post-monsoon — Ganesha festival
    10: 1.25,   # Dasara — peak festival crime
    11: 1.20,   # Diwali, Rajyotsava
    12: 1.10,   # Christmas, end-year travel
}

# Karnataka public holidays
KARNATAKA_HOLIDAYS: List[Dict] = [
    {"month": 1,  "day": 26, "name": "Republic Day"},
    {"month": 3,  "day": 22, "name": "Ugadi"},         # approximate
    {"month": 4,  "day": 14, "name": "Dr. Ambedkar Jayanti"},
    {"month": 4,  "day": 10, "name": "Eid al-Fitr"},   # approximate
    {"month": 5,  "day": 1,  "name": "May Day"},
    {"month": 6,  "day": 17, "name": "Bakrid"},         # approximate
    {"month": 8,  "day": 15, "name": "Independence Day"},
    {"month": 9,  "day": 16, "name": "Milad-un-Nabi"},  # approximate
    {"month": 10, "day": 2,  "name": "Gandhi Jayanti"},
    {"month": 11, "day": 1,  "name": "Rajyotsava"},
    {"month": 11, "day": 1,  "name": "Diwali"},         # approximate
    {"month": 12, "day": 25, "name": "Christmas"},
]


class DayContext:
    """Encapsulates the risk context for a single simulation day."""

    def __init__(
        self,
        date_: date,
        is_holiday: bool,
        is_weekend: bool,
        festival: Optional[str],
        season: str,
        crime_multipliers: Dict[str, float],
    ) -> None:
        self.date = date_
        self.is_holiday = is_holiday
        self.is_weekend = is_weekend
        self.festival = festival
        self.season = season
        self.crime_multipliers = crime_multipliers  # crime_type_id → multiplier

    @property
    def is_high_risk_day(self) -> bool:
        return any(v >= 1.5 for v in self.crime_multipliers.values())

    @property
    def overall_risk(self) -> float:
        if not self.crime_multipliers:
            return 1.0
        return sum(self.crime_multipliers.values()) / len(self.crime_multipliers)


class KarnatakaCalendar:
    """
    Provides crime risk context for any given date.
    Pre-computes festival windows for fast lookup.
    """

    def __init__(self) -> None:
        self._festival_windows: List[Dict] = []
        self._holiday_set: set = set()
        self._precompute_festivals()
        self._precompute_holidays()

    def _precompute_festivals(self) -> None:
        """Build a list of (start_date, end_date, festival_name, risk_map) tuples."""
        for year in range(2018, 2030):
            for fest in FESTIVALS:
                try:
                    start = date(year, fest["month"], fest["day"])
                    end = start + timedelta(days=fest.get("duration_days", 1) - 1)
                    self._festival_windows.append({
                        "start": start,
                        "end": end,
                        "name": fest["name"],
                        "risk": fest["risk"],
                    })
                except ValueError:
                    pass  # Invalid date (e.g., Feb 30)

    def _precompute_holidays(self) -> None:
        """Build a set of (month, day) tuples for public holidays."""
        for h in KARNATAKA_HOLIDAYS:
            self._holiday_set.add((h["month"], h["day"]))

    def _get_season(self, month: int) -> str:
        if month in {12, 1, 2}:
            return "winter"
        elif month in {3, 4, 5}:
            return "summer"
        elif month in {6, 7, 8, 9}:
            return "monsoon"
        else:
            return "post_monsoon"

    def get_day_context(self, d: date) -> DayContext:
        """Return the full risk context for a given date."""
        is_weekend = d.weekday() >= 5  # Saturday or Sunday
        is_holiday = (d.month, d.day) in self._holiday_set

        # Find active festivals
        active_festival: Optional[str] = None
        festival_risk: Dict[str, float] = {}
        for fw in self._festival_windows:
            if fw["start"] <= d <= fw["end"]:
                active_festival = fw["name"]
                for crime_type, mult in fw["risk"].items():
                    festival_risk[crime_type] = max(festival_risk.get(crime_type, 1.0), mult)

        # Compute per-crime-type multipliers
        monthly_mult = MONTHLY_BASELINE.get(d.month, 1.0)
        weekend_mult = 1.15 if is_weekend else 1.0
        holiday_mult = 1.20 if is_holiday else 1.0

        crime_multipliers: Dict[str, float] = {}
        for cat in CRIME_CATEGORIES:
            ctype = cat["id"]
            base = monthly_mult * weekend_mult * holiday_mult
            fest_mod = festival_risk.get(ctype, 1.0)
            crime_multipliers[ctype] = round(base * fest_mod, 3)

        return DayContext(
            date_=d,
            is_holiday=is_holiday,
            is_weekend=is_weekend,
            festival=active_festival,
            season=self._get_season(d.month),
            crime_multipliers=crime_multipliers,
        )
