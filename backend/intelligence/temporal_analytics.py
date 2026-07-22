"""
Temporal Analytics Engine — Phase 7.0

Detects crime spikes, seasonal patterns, coordinated events, and
recurring offender schedules using statistical time-series methods.

Algorithms used:
    - Rolling window averages (7-day, 30-day) via pandas
    - CUSUM (Cumulative Sum Control Chart) for changepoint detection
    - Coordinated event window: multiple FIRs in same district ≤ N hours apart
    - Seasonal index: frequency by month/day-of-week

All results carry full IntelligenceExplanation provenance.
Deterministic: same input → same output.
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional
from datetime import date, timedelta
import calendar

import pandas as pd
import numpy as np
from sqlalchemy.orm import Session

from backend.db.schema import FIR
from backend.intelligence.confidence import ConfidenceScore
from backend.intelligence.explainability import (
    IntelligenceExplanation, EvidenceItem, InferenceType
)

# CUSUM parameters
CUSUM_K = 0.5      # allowable slack (half of expected shift)
CUSUM_H = 4.0      # decision threshold (standard deviations)

# FIX MEDIUM #1: Seasonal multipliers for crime baseline (month-based)
# Adjusts expected crime count by season to avoid false alarms
SEASONAL_MULTIPLIERS = {
    1: 0.85,   # January (winter, low)
    2: 0.85,   # February (winter, low)
    3: 0.95,   # March (spring, rising)
    4: 1.00,   # April (spring, normal)
    5: 1.05,   # May (summer, rising)
    6: 1.15,   # June (summer, high)
    7: 1.25,   # July (peak summer)
    8: 1.20,   # August (summer)
    9: 1.05,   # September (fall)
    10: 1.10,  # October (festival season - Diwali)
    11: 1.15,  # November (festival, high)
    12: 1.20,  # December (winter holidays, high)
}

# Coordinated event window
COORD_WINDOW_HOURS = 6
COORD_MIN_EVENTS   = 3


class TemporalAnalyticsEngine:
    """
    Temporal analytics for crime time-series data.

    Usage:
        engine = TemporalAnalyticsEngine(db)
        alerts = engine.detect_anomalies(district_id="DIST-01", days=90)
    """

    def __init__(self, db: Session):
        self.db = db

    def detect_anomalies(
        self,
        district_id: Optional[str] = None,
        days: int = 90,
        granularity: str = "daily",  # FIX MEDIUM #2: Allow hourly option
    ) -> Dict[str, Any]:
        """
        Run full temporal analysis for a district and return all anomaly alerts.
        FIX MEDIUM #2: Supports daily (default) or hourly granularity.
        """
        firs = self._fetch_firs(district_id, days)
        if len(firs) < 7:
            return {"alerts": [], "message": "Insufficient data for temporal analysis"}

        df = self._to_dataframe(firs)

        alerts = []
        if granularity == "hourly":
            # FIX MEDIUM #2: Add hourly spike detection for intra-day anomalies
            alerts.extend(self._detect_spikes_hourly(df, district_id))
        else:
            # Default daily detection
            alerts.extend(self._detect_spikes(df, district_id))

        alerts.extend(self._detect_coordinated_events(df, district_id))

        seasonal = self._seasonal_profile(df)
        rollup = self._rolling_summary(df)

        return {
            "alerts": alerts,
            "total_alerts": len(alerts),
            "rolling_summary": rollup,
            "seasonal_profile": seasonal,
            "analysis_period_days": days,
            "granularity": granularity,
            "district_id": district_id,
            "firs_analyzed": len(firs),
        }

    def offender_schedule(self, criminal_id: str) -> Dict[str, Any]:
        """
        Analyze a specific criminal's temporal activity pattern.
        Returns preferred time slots, days, and activity concentration.
        """
        from backend.db.schema import FIRAccomplice
        rows = self.db.query(FIRAccomplice).filter_by(criminal_id=criminal_id).all()
        fir_ids = [r.fir_id for r in rows]
        if not fir_ids:
            return {"criminal_id": criminal_id, "schedule": None, "error": "No FIR history"}

        firs = self.db.query(FIR).filter(FIR.fir_id.in_(fir_ids)).all()
        df = self._to_dataframe(firs)
        if df.empty:
            return {"criminal_id": criminal_id, "schedule": {}}

        by_dow = df.groupby("day_of_week").size().to_dict()
        by_month = df.groupby("month").size().to_dict()

        dominant_dow = max(by_dow, key=by_dow.get) if by_dow else None
        dow_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        return {
            "criminal_id": criminal_id,
            "fir_count": len(firs),
            "activity_by_day_of_week": {dow_names[int(k)]: v for k, v in by_dow.items()},
            "activity_by_month": {str(k): v for k, v in by_month.items()},
            "dominant_day": dow_names[int(dominant_dow)] if dominant_dow is not None else None,
        }

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    def _fetch_firs(self, district_id: Optional[str], days: int) -> List[FIR]:
        cutoff = date.today() - timedelta(days=days)
        q = self.db.query(FIR).filter(FIR.occurred_date >= cutoff)
        if district_id:
            q = q.filter(FIR.district_id == district_id)
        return q.order_by(FIR.occurred_date).all()

    def _to_dataframe(self, firs: List[FIR]) -> pd.DataFrame:
        rows = []
        for f in firs:
            if not f.occurred_date:
                continue
            d = f.occurred_date
            # FIX MEDIUM #2: Include hour from occurred_time if available
            hour = 12  # Default noon
            if f.occurred_time:
                hour = f.occurred_time.hour
            rows.append({
                "fir_id": f.fir_id,
                "date": pd.Timestamp(d),
                "hour": hour,
                "day_of_week": d.weekday(),
                "month": d.month,
                "crime_category": f.crime_category or "Unknown",
                "district_id": f.district_id or "",
                "is_gang_crime": bool(f.is_gang_crime),
            })
        return pd.DataFrame(rows)

    def _detect_spikes_hourly(self, df: pd.DataFrame, district_id: Optional[str]) -> List[Dict]:
        """
        FIX MEDIUM #2: Detect intra-day spikes (e.g., 2–4 AM crime burst).
        Requires occurred_time (hour:minute) precision from FIRs.
        """
        if df.empty or "hour" not in df.columns:
            return []

        hourly = df.groupby("hour").size().reset_index(name="count")
        counts = hourly["count"].values.astype(float)

        if len(counts) < 4:  # Need at least 4 hours
            return []

        mu = float(np.mean(counts))
        sigma = float(np.std(counts)) or 1.0

        # CUSUM on hourly data (lower h threshold due to higher variance)
        S_pos = np.zeros(len(counts))
        h_hourly = 2.5  # Lower threshold for hourly data
        for i in range(1, len(counts)):
            S_pos[i] = max(0.0, S_pos[i - 1] + (counts[i] - mu) / sigma - CUSUM_K)

        spike_indices = np.where(S_pos > h_hourly)[0]
        if len(spike_indices) == 0:
            return []

        alerts = []
        spike_hour = int(hourly.iloc[spike_indices[0]]["hour"])
        spike_count = int(counts[spike_indices[0]])

        conf = ConfidenceScore(
            evidence_quality=min(1.0, spike_count / (mu + 1)),
            data_completeness=0.8,  # Hourly data may be sparser
            algorithm_confidence=0.75,
            source_reliability=0.95,
            recency_weight=0.90,
        ).compute()

        evidence = [
            EvidenceItem(
                dimension="hourly_cusum",
                description=f"Hourly spike at {spike_hour:02d}:00 with CUSUM {S_pos[spike_indices[0]]:.2f}",
                raw_value=float(S_pos[spike_indices[0]]),
                weight=0.7,
                contributed_score=min(1.0, S_pos[spike_indices[0]] / 5) * 0.7,
            ),
            EvidenceItem(
                dimension="hourly_volume",
                description=f"Hour {spike_hour:02d}:00 saw {spike_count} crimes vs hourly mean {mu:.1f}",
                raw_value=spike_count,
                weight=0.3,
                contributed_score=min(1.0, (spike_count - mu) / (sigma + 1)) * 0.3,
            ),
        ]

        explanation = IntelligenceExplanation(
            inference_type=InferenceType.TEMPORAL_ANOMALY,
            observation=f"Intra-day crime spike detected during hour {spike_hour:02d}:00–{(spike_hour+1)%24:02d}:00",
            evidence=evidence,
            analytical_rule=f"Hourly CUSUM (k={CUSUM_K}, h=2.5)",
            inference=f"Unusual concentration of {spike_count} crimes in a single hour (vs {mu:.1f} avg)",
            confidence=conf,
            recommended_action=f"Investigate crimes occurring in hour {spike_hour:02d}:00; consider coordinated incident or gang activity",
        )

        alerts.append({
            "alert_type": "INTRADAY_SPIKE",
            "hour": spike_hour,
            "crime_count": spike_count,
            "baseline_hourly_mean": round(mu, 2),
            "severity": "HIGH" if spike_count > mu * 2 else "MEDIUM",
            "confidence": conf.to_dict(),
            "explanation": explanation.to_dict(),
        })

        return alerts

    def _detect_spikes(self, df: pd.DataFrame, district_id: Optional[str]) -> List[Dict]:
        """
        FIX MEDIUM #1: CUSUM changepoint detection with seasonal adjustment.
        Accounts for predictable crime spikes (summer, festivals) to reduce false alarms.
        """
        if df.empty:
            return []

        daily = df.groupby("date").size().reset_index(name="count")
        daily = daily.set_index("date").sort_index()
        daily = daily.asfreq("D", fill_value=0)

        counts = daily["count"].values.astype(float)
        if len(counts) < 7:
            return []

        # FIX: Adjust baseline by seasonal multiplier
        seasonal_adjusted_counts = []
        for date_idx, count in zip(daily.index, counts):
            month = date_idx.month
            seasonal_factor = SEASONAL_MULTIPLIERS.get(month, 1.0)
            adjusted_count = count / seasonal_factor  # Normalize out seasonality
            seasonal_adjusted_counts.append(adjusted_count)

        seasonal_adjusted_counts = np.array(seasonal_adjusted_counts)
        mu = float(np.mean(seasonal_adjusted_counts))
        sigma = float(np.std(seasonal_adjusted_counts)) or 1.0

        # CUSUM upper (detects upward shifts)
        S_pos = np.zeros(len(seasonal_adjusted_counts))
        for i in range(1, len(seasonal_adjusted_counts)):
            S_pos[i] = max(0.0, S_pos[i - 1] + (seasonal_adjusted_counts[i] - mu) / sigma - CUSUM_K)

        spike_indices = np.where(S_pos > CUSUM_H)[0]
        if len(spike_indices) == 0:
            return []

        alerts = []
        spike_date = daily.index[spike_indices[0]]
        spike_count = int(counts[spike_indices[0]])
        spike_month = spike_date.month
        is_seasonal = SEASONAL_MULTIPLIERS.get(spike_month, 1.0) > 1.05  # Elevated season

        conf = ConfidenceScore(
            evidence_quality=min(1.0, spike_count / (mu + 1)),
            data_completeness=min(1.0, len(counts) / 30),
            algorithm_confidence=0.82 if not is_seasonal else 0.70,  # Lower confidence for seasonal
            source_reliability=0.95,
            recency_weight=ConfidenceScore.recency_factor(spike_date.date()),
        ).compute()

        seasonal_note = ""
        if is_seasonal:
            seasonal_factor = SEASONAL_MULTIPLIERS.get(spike_month, 1.0)
            seasonal_note = f" (Month {spike_month} is seasonally elevated by {(seasonal_factor-1)*100:.0f}%)"

        evidence = [
            EvidenceItem(
                dimension="cusum_statistic",
                description=f"CUSUM statistic {S_pos[spike_indices[0]]:.2f} exceeded threshold {CUSUM_H}",
                raw_value=float(S_pos[spike_indices[0]]),
                weight=0.6,
                contributed_score=min(1.0, S_pos[spike_indices[0]] / 10) * 0.6,
            ),
            EvidenceItem(
                dimension="daily_volume",
                description=f"Daily count {spike_count} vs seasonal-adjusted baseline {mu:.1f}{seasonal_note}",
                raw_value=spike_count,
                weight=0.4,
                contributed_score=min(1.0, (spike_count - mu) / (sigma + 1)) * 0.4,
            ),
        ]

        if is_seasonal:
            evidence.append(EvidenceItem(
                dimension="seasonal_context",
                description=f"Alert occurs during seasonally elevated month ({list(calendar.month_name)[spike_month]}). May be normal seasonal variation.",
                raw_value=SEASONAL_MULTIPLIERS.get(spike_month, 1.0),
                weight=0.0,
                contributed_score=0.0,
            ))

        explanation = IntelligenceExplanation(
            inference_type=InferenceType.TEMPORAL_ANOMALY,
            observation=f"Daily crime count rose sharply near {spike_date.strftime('%Y-%m-%d')}",
            evidence=evidence,
            analytical_rule=f"CUSUM(k={CUSUM_K}, h={CUSUM_H}) on seasonal-adjusted baseline",
            inference=f"Crime spike detected in {'district ' + district_id if district_id else 'all districts'} starting {spike_date.strftime('%Y-%m-%d')}",
            confidence=conf,
            recommended_action="Increase patrol density in affected area; cross-reference FIRs for shared accused" + (
                "; note: spike occurs during seasonally elevated period" if is_seasonal else ""
            ),
        )

        alerts.append({
            "alert_type": "CRIME_SPIKE",
            "date": spike_date.strftime("%Y-%m-%d"),
            "affected_district": district_id,
            "daily_count": spike_count,
            "baseline_mean": round(mu, 2),
            "severity": "HIGH" if S_pos[spike_indices[0]] > CUSUM_H * 2 else "MEDIUM",
            "confidence": conf.to_dict(),
            "explanation": explanation.to_dict(),
        })
        return alerts

    def _detect_coordinated_events(
        self, df: pd.DataFrame, district_id: Optional[str]
    ) -> List[Dict]:
        """Detect bursts of multiple FIRs within a short time window (same day proxy)."""
        if df.empty:
            return []

        daily = df.groupby("date").size()
        alerts = []

        for d, count in daily.items():
            if count >= COORD_MIN_EVENTS:
                involved_firs = df[df["date"] == d]["fir_id"].tolist()
                conf = ConfidenceScore(
                    evidence_quality=min(1.0, count / 10),
                    data_completeness=1.0,
                    algorithm_confidence=0.70,
                    source_reliability=0.95,
                    recency_weight=ConfidenceScore.recency_factor(d.date()),
                ).compute()

                evidence = [EvidenceItem(
                    dimension="event_burst",
                    description=f"{count} FIRs recorded on {d.strftime('%Y-%m-%d')} (threshold: {COORD_MIN_EVENTS})",
                    raw_value=count,
                    weight=1.0,
                    contributed_score=min(1.0, count / 10),
                )]

                explanation = IntelligenceExplanation(
                    inference_type=InferenceType.TEMPORAL_ANOMALY,
                    observation=f"{count} FIRs filed on {d.strftime('%Y-%m-%d')}",
                    evidence=evidence,
                    analytical_rule=f"Event burst detection (≥{COORD_MIN_EVENTS} FIRs within same day)",
                    inference="Possible coordinated criminal campaign or mass incident on this date",
                    confidence=conf,
                    recommended_action="Cross-reference accused in all FIRs for shared individuals",
                )

                alerts.append({
                    "alert_type": "COORDINATED_EVENT",
                    "date": d.strftime("%Y-%m-%d"),
                    "affected_district": district_id,
                    "fir_count": count,
                    "fir_ids": involved_firs[:20],
                    "severity": "HIGH" if count >= 8 else "MEDIUM",
                    "confidence": conf.to_dict(),
                    "explanation": explanation.to_dict(),
                })

        return alerts

    def _rolling_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        if df.empty:
            return {}
        daily = df.groupby("date").size()
        roll7  = daily.rolling(7).mean().iloc[-1] if len(daily) >= 7 else None
        roll30 = daily.rolling(30).mean().iloc[-1] if len(daily) >= 30 else None
        return {
            "7_day_rolling_avg": round(float(roll7), 2) if roll7 is not None else None,
            "30_day_rolling_avg": round(float(roll30), 2) if roll30 is not None else None,
            "total_in_period": int(daily.sum()),
            "peak_day": daily.idxmax().strftime("%Y-%m-%d") if not daily.empty else None,
            "peak_count": int(daily.max()) if not daily.empty else 0,
        }

    def _seasonal_profile(self, df: pd.DataFrame) -> Dict[str, Any]:
        if df.empty:
            return {}
        by_dow = df.groupby("day_of_week").size().to_dict()
        by_month = df.groupby("month").size().to_dict()
        dow_names = ["Monday", "Tuesday", "Wednesday", "Thursday",
                     "Friday", "Saturday", "Sunday"]
        return {
            "by_day_of_week": {dow_names[int(k)]: int(v) for k, v in sorted(by_dow.items())},
            "by_month": {str(k): int(v) for k, v in sorted(by_month.items())},
        }
