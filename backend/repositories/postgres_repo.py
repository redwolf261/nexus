from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from backend.db.schema import (
    Accused, Arrest, Campaign, CCTVLog, Criminal, District, Evidence,
    FIR, FIRPhone, FIRVehicle, Gang, GangMember, InvestigationLog,
    Mastermind, Officer, PatrolLog, Person, Phone, Station, Vehicle,
    Victim,
)


class PostgresRepository:
    def __init__(self, db: Session):
        self.db = db

    # ── FIRs ──────────────────────────────────────────────────────────────────

    def get_firs(
        self,
        district_id: Optional[str] = None,
        crime_type: Optional[str] = None,
        crime_category: Optional[str] = None,
        status: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        is_gang_crime: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[FIR]:
        q = self.db.query(FIR)
        if district_id:
            q = q.filter(FIR.district_id == district_id)
        if crime_type:
            q = q.filter(FIR.crime_type == crime_type)
        if crime_category:
            q = q.filter(FIR.crime_category == crime_category)
        if status:
            q = q.filter(FIR.status == status)
        if date_from:
            q = q.filter(FIR.occurred_date >= date_from)
        if date_to:
            q = q.filter(FIR.occurred_date <= date_to)
        if is_gang_crime is not None:
            q = q.filter(FIR.is_gang_crime == is_gang_crime)
        return q.order_by(FIR.occurred_date.desc()).limit(limit).offset(offset).all()

    def get_fir_by_id(self, fir_id: str) -> Optional[FIR]:
        return self.db.query(FIR).filter(FIR.fir_id == fir_id).first()

    def get_fir_detail(self, fir_id: str) -> Dict[str, Any]:
        """Return FIR + aggregated child counts for the investigation drawer."""
        fir = self.db.query(FIR).filter(FIR.fir_id == fir_id).first()
        if not fir:
            return {}
        accused_rows = (
            self.db.query(Accused).filter(Accused.fir_id == fir_id).all()
        )
        victim_rows = (
            self.db.query(Victim).filter(Victim.fir_id == fir_id).all()
        )
        evidence_count = (
            self.db.query(func.count(Evidence.evidence_id))
            .filter(Evidence.fir_id == fir_id)
            .scalar()
        )
        inv_logs = (
            self.db.query(InvestigationLog)
            .filter(InvestigationLog.fir_id == fir_id)
            .order_by(InvestigationLog.timestamp)
            .all()
        )
        # Vehicles and phones linked via junction tables
        linked_vehicles = (
            self.db.query(Vehicle)
            .join(FIRVehicle, FIRVehicle.vehicle_id == Vehicle.vehicle_id)
            .filter(FIRVehicle.fir_id == fir_id)
            .all()
        )
        linked_phones = (
            self.db.query(Phone)
            .join(FIRPhone, FIRPhone.phone_id == Phone.phone_id)
            .filter(FIRPhone.fir_id == fir_id)
            .all()
        )
        return {
            "fir": fir,
            "accused": accused_rows,
            "victims": victim_rows,
            "evidence_count": evidence_count or 0,
            "investigation_logs": inv_logs,
            "linked_vehicles": linked_vehicles,
            "linked_phones": linked_phones,
        }

    def get_fir_coordinates(self, limit: int = 2000) -> List[Tuple[float, float]]:
        """Return (lat, lng) pairs for DBSCAN hotspot computation."""
        rows = (
            self.db.query(FIR.latitude, FIR.longitude)
            .filter(FIR.latitude.isnot(None), FIR.longitude.isnot(None))
            .limit(limit)
            .all()
        )
        return [(r.latitude, r.longitude) for r in rows]

    # ── Persons ───────────────────────────────────────────────────────────────

    def get_person_by_id(self, citizen_id: str) -> Optional[Person]:
        return self.db.query(Person).filter(Person.citizen_id == citizen_id).first()

    # ── Officers ──────────────────────────────────────────────────────────────

    def get_officer_by_id(self, officer_id: str) -> Optional[Officer]:
        return self.db.query(Officer).filter(Officer.officer_id == officer_id).first()

    def get_officer_stats(self, officer_id: str) -> Dict[str, Any]:
        """Return real case-load statistics for a given officer."""
        officer = self.get_officer_by_id(officer_id)
        if not officer:
            return {}

        # FIRs this officer is investigating
        investigating = (
            self.db.query(func.count(FIR.fir_id))
            .filter(FIR.investigating_officer_id == officer_id)
            .scalar()
            or 0
        )
        open_cases = (
            self.db.query(func.count(FIR.fir_id))
            .filter(
                FIR.investigating_officer_id == officer_id,
                FIR.status.in_(["Under Investigation", "Open"]),
            )
            .scalar()
            or 0
        )
        closed_cases = investigating - open_cases

        # Patrol coverage: distinct areas this officer has patrolled
        patrol_areas = (
            self.db.query(PatrolLog.beat_area)
            .filter(PatrolLog.officer_id == officer_id)
            .distinct()
            .limit(3)
            .all()
        )
        area_str = (
            ", ".join(r.beat_area for r in patrol_areas if r.beat_area)
            or officer.district_name or "Unknown"
        )

        # Average delay: days between occurred_date and reported_date
        avg_delay = (
            self.db.query(
                func.avg(
                    func.julianday(FIR.reported_date) - func.julianday(FIR.occurred_date)
                )
            )
            .filter(
                FIR.investigating_officer_id == officer_id,
                FIR.reported_date.isnot(None),
                FIR.occurred_date.isnot(None),
            )
            .scalar()
        )

        workload = (
            "Critical" if open_cases > 20
            else "High" if open_cases > 10
            else "Medium" if open_cases > 5
            else "Low"
        )

        return {
            "officer_id": officer_id,
            "cases_open": open_cases,
            "cases_closed": closed_cases,
            "average_delay_days": round(float(avg_delay), 1) if avg_delay else 0.0,
            "workload": workload,
            "patrol_area": area_str,
        }

    # ── Search ────────────────────────────────────────────────────────────────

    def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """ILIKE search across FIRs, persons, vehicles, criminals."""
        results: List[Dict[str, Any]] = []
        like = f"%{query}%"

        firs = (
            self.db.query(FIR)
            .filter(
                FIR.fir_number.ilike(like)
                | FIR.description_en.ilike(like)
                | FIR.crime_type.ilike(like)
                | FIR.complainant_name.ilike(like)
            )
            .limit(limit)
            .all()
        )
        for f in firs:
            results.append({
                "type": "FIR",
                "id": f.fir_id,
                "name": f.fir_number or f.fir_id,
                "snippet": f"{f.crime_type} · {f.district_name} · {f.status}",
            })

        persons = (
            self.db.query(Person)
            .filter(
                Person.name_en.ilike(like)
                | Person.phone_primary.ilike(like)
                | Person.occupation.ilike(like)
            )
            .limit(limit)
            .all()
        )
        for p in persons:
            results.append({
                "type": "Person",
                "id": p.citizen_id,
                "name": p.name_en or p.citizen_id,
                "snippet": f"{p.occupation} · {p.district_name}",
            })

        vehicles = (
            self.db.query(Vehicle)
            .filter(
                Vehicle.license_plate.ilike(like)
                | Vehicle.make.ilike(like)
                | Vehicle.model.ilike(like)
            )
            .limit(limit)
            .all()
        )
        for v in vehicles:
            results.append({
                "type": "Vehicle",
                "id": v.vehicle_id,
                "name": v.license_plate or v.vehicle_id,
                "snippet": f"{v.color} {v.make} {v.model}"
                + (" · STOLEN" if v.is_stolen else ""),
            })

        criminals = (
            self.db.query(Criminal)
            .filter(
                Criminal.name_en.ilike(like)
                | Criminal.alias_names.ilike(like)
                | Criminal.expertise.ilike(like)
            )
            .limit(limit)
            .all()
        )
        for c in criminals:
            results.append({
                "type": "Criminal",
                "id": c.criminal_id,
                "name": c.name_en or c.criminal_id,
                "snippet": f"{c.risk_level} risk · {c.district_name}",
            })

        return results[:limit]

    # ── Executive Dashboard ───────────────────────────────────────────────────

    def get_executive_kpis(self) -> Dict[str, Any]:
        """Aggregate KPIs for the landing page dashboard."""
        today = date.today()
        thirty_days_ago = today - timedelta(days=30)

        total_firs = (
            self.db.query(func.count(FIR.fir_id)).scalar() or 0
        )
        recent_firs = (
            self.db.query(func.count(FIR.fir_id))
            .filter(FIR.occurred_date >= thirty_days_ago)
            .scalar()
            or 0
        )
        active_campaigns = (
            self.db.query(func.count(Campaign.campaign_id))
            .filter(Campaign.status != "completed")
            .scalar()
            or 0
        )
        # Average investigation time: days from occurred_date to last inv_log
        # Approximate via reported_date as proxy
        avg_days_row = (
            self.db.query(
                func.avg(
                    func.julianday(FIR.reported_date) - func.julianday(FIR.occurred_date)
                )
            )
            .filter(
                FIR.reported_date.isnot(None),
                FIR.occurred_date.isnot(None),
            )
            .scalar()
        )
        avg_inv_time = round(float(avg_days_row), 1) if avg_days_row else 0.0

        # Count distinct gang crimes in last 30 days as "intelligence alerts"
        new_alerts = (
            self.db.query(func.count(FIR.fir_id))
            .filter(
                FIR.is_gang_crime == True,
                FIR.occurred_date >= thirty_days_ago,
            )
            .scalar()
            or 0
        )

        # Crime trend: compare last 30 days vs prior 30 days
        prior_30 = today - timedelta(days=60)
        prior_count = (
            self.db.query(func.count(FIR.fir_id))
            .filter(
                FIR.occurred_date >= prior_30,
                FIR.occurred_date < thirty_days_ago,
            )
            .scalar()
            or 1
        )
        change_pct = round((recent_firs - prior_count) / prior_count * 100, 1)
        trend_dir = "up" if change_pct >= 0 else "down"
        trend_str = f"{abs(change_pct)}% {trend_dir} vs prior 30 days"

        return {
            "todays_firs": recent_firs,
            "active_campaigns": active_campaigns,
            "predicted_hotspots": 0,  # filled by hotspot service
            "average_investigation_time": avg_inv_time,
            "crime_trend": trend_str,
            "new_intelligence_alerts": new_alerts,
            "total_firs": total_firs,
        }

    # ── District Dashboard ────────────────────────────────────────────────────

    def get_district_stats(self, district_id: str) -> Dict[str, Any]:
        """Per-district analytics for district dashboard."""
        total_firs = (
            self.db.query(func.count(FIR.fir_id))
            .filter(FIR.district_id == district_id)
            .scalar()
            or 0
        )

        # Top crime type
        top_crime_row = (
            self.db.query(FIR.crime_type, func.count(FIR.fir_id).label("cnt"))
            .filter(FIR.district_id == district_id)
            .group_by(FIR.crime_type)
            .order_by(text("cnt DESC"))
            .first()
        )
        top_crime = top_crime_row.crime_type if top_crime_row else "Unknown"

        # Active gangs in this district (via campaigns)
        gang_rows = (
            self.db.query(Gang.name)
            .join(Campaign, Campaign.gang_id == Gang.gang_id)
            .filter(Campaign.target_district_id == district_id)
            .distinct()
            .limit(5)
            .all()
        )
        top_gangs = [r.name for r in gang_rows] if gang_rows else []
        active_gang_count = len(top_gangs)

        # Repeat offenders: criminals with >1 crime in this district
        repeat_offenders = (
            self.db.query(func.count(Criminal.criminal_id))
            .filter(
                Criminal.district_id == district_id,
                Criminal.total_crimes_committed > 1,
            )
            .scalar()
            or 0
        )

        # Risk score: normalized 0-100 based on total FIRs relative to max district
        max_firs_row = (
            self.db.query(func.count(FIR.fir_id).label("cnt"))
            .group_by(FIR.district_id)
            .order_by(text("cnt DESC"))
            .first()
        )
        max_firs = max_firs_row.cnt if max_firs_row else 1
        risk_score = min(100, int(total_firs / max_firs * 100))

        # Patrol coverage
        patrol_entries = (
            self.db.query(func.count(PatrolLog.log_id))
            .filter(PatrolLog.district_id == district_id)
            .scalar()
            or 0
        )
        # Approximate coverage quality
        coverage_str = (
            "Optimal" if patrol_entries > 1000
            else "Good" if patrol_entries > 500
            else "Moderate" if patrol_entries > 100
            else "Low"
        )

        return {
            "district_id": district_id,
            "total_firs": total_firs,
            "top_gangs": top_gangs,
            "active_gang_count": active_gang_count,
            "repeat_offenders": repeat_offenders,
            "risk_score": risk_score,
            "patrol_coverage": coverage_str,
            "crime_trend": f"Spike in {top_crime} detected" if top_crime != "Unknown" else "No dominant trend",
        }

    # ── Campaign ──────────────────────────────────────────────────────────────

    def get_campaign_detail(self, campaign_id: str) -> Dict[str, Any]:
        """Return campaign + gang + mastermind + linked assets."""
        campaign = (
            self.db.query(Campaign)
            .filter(Campaign.campaign_id == campaign_id)
            .first()
        )
        if not campaign:
            return {}

        gang = (
            self.db.query(Gang)
            .filter(Gang.gang_id == campaign.gang_id)
            .first()
            if campaign.gang_id else None
        )

        mastermind = (
            self.db.query(Mastermind)
            .filter(Mastermind.controlled_gang_ids.contains(campaign.gang_id))
            .first()
            if campaign.gang_id else None
        )

        # Vehicles linked to FIRs in this campaign
        vehicle_plates = (
            self.db.query(Vehicle.license_plate)
            .join(FIRVehicle, FIRVehicle.vehicle_id == Vehicle.vehicle_id)
            .join(FIR, FIR.fir_id == FIRVehicle.fir_id)
            .filter(FIR.campaign_id == campaign_id)
            .distinct()
            .limit(10)
            .all()
        )
        # Phones linked to FIRs in this campaign
        phone_numbers = (
            self.db.query(Phone.phone_number)
            .join(FIRPhone, FIRPhone.phone_id == Phone.phone_id)
            .join(FIR, FIR.fir_id == FIRPhone.fir_id)
            .filter(FIR.campaign_id == campaign_id)
            .distinct()
            .limit(10)
            .all()
        )

        timeline_count = (
            self.db.query(func.count(FIR.fir_id))
            .filter(FIR.campaign_id == campaign_id)
            .scalar()
            or 0
        )

        return {
            "campaign_id": campaign_id,
            "gang_id": campaign.gang_id or "",
            "gang_name": gang.name if gang else "Unknown",
            "crime_category": campaign.crime_category or "",
            "start_date": str(campaign.start_date) if campaign.start_date else None,
            "end_date": str(campaign.end_date) if campaign.end_date else None,
            "num_crimes_planned": campaign.num_crimes_planned or 0,
            "num_crimes_committed": campaign.num_crimes_committed or 0,
            "status": campaign.status or "Unknown",
            "mastermind": mastermind.name_en if mastermind else (gang.leader_criminal_id if gang else "Unidentified"),
            "mastermind_alias": mastermind.alias if mastermind else None,
            "vehicles": [r.license_plate for r in vehicle_plates if r.license_plate],
            "phones": [r.phone_number for r in phone_numbers if r.phone_number],
            "timeline_events": timeline_count,
        }

    # ── Entity Detail (Investigation Drawer) ─────────────────────────────────

    def get_fir_full(self, fir_id: str) -> Dict[str, Any]:
        """Full FIR detail including accused, victims, evidence, inv logs, linked assets."""
        return self.get_fir_detail(fir_id)

    def get_person_full(self, person_id: str) -> Dict[str, Any]:
        """Person profile + criminal record + linked FIRs."""
        person = self.db.query(Person).filter(Person.citizen_id == person_id).first()
        if not person:
            return {}

        criminal = (
            self.db.query(Criminal)
            .filter(Criminal.citizen_id == person_id)
            .first()
        )

        linked_firs = (
            self.db.query(FIR)
            .filter(FIR.primary_criminal_id == (criminal.criminal_id if criminal else None))
            .order_by(FIR.occurred_date.desc())
            .limit(10)
            .all()
        ) if criminal else []

        vehicles = (
            self.db.query(Vehicle)
            .filter(Vehicle.owner_id == person_id)
            .all()
        )

        phones = (
            self.db.query(Phone)
            .filter(Phone.owner_id == person_id)
            .all()
        )

        gang = None
        if criminal and criminal.gang_id:
            gang = self.db.query(Gang).filter(Gang.gang_id == criminal.gang_id).first()

        return {
            "person": person,
            "criminal": criminal,
            "linked_firs": linked_firs,
            "vehicles": vehicles,
            "phones": phones,
            "gang": gang,
        }

    def get_vehicle_full(self, vehicle_id: str) -> Dict[str, Any]:
        """Vehicle + owner + linked FIRs via junction table."""
        vehicle = self.db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()
        if not vehicle:
            return {}

        owner = (
            self.db.query(Person)
            .filter(Person.citizen_id == vehicle.owner_id)
            .first()
        ) if vehicle.owner_id else None

        linked_firs = (
            self.db.query(FIR)
            .join(FIRVehicle, FIRVehicle.fir_id == FIR.fir_id)
            .filter(FIRVehicle.vehicle_id == vehicle_id)
            .order_by(FIR.occurred_date.desc())
            .limit(10)
            .all()
        )

        return {
            "vehicle": vehicle,
            "owner": owner,
            "linked_firs": linked_firs,
        }

    def get_criminal_full(self, criminal_id: str) -> Dict[str, Any]:
        """Full criminal profile including gang, MO, associates, and linked FIRs."""
        criminal = (
            self.db.query(Criminal)
            .filter(Criminal.criminal_id == criminal_id)
            .first()
        )
        if not criminal:
            return {}

        gang = (
            self.db.query(Gang)
            .filter(Gang.gang_id == criminal.gang_id)
            .first()
        ) if criminal.gang_id else None

        # FIRs where this criminal is the primary accused
        linked_firs = (
            self.db.query(FIR)
            .filter(FIR.primary_criminal_id == criminal_id)
            .order_by(FIR.occurred_date.desc())
            .limit(10)
            .all()
        )

        # Associates from junction table
        associates = (
            self.db.query(Criminal)
            .join(
                CriminalAssociate,
                CriminalAssociate.associate_id == Criminal.criminal_id,
            )
            .filter(CriminalAssociate.criminal_id == criminal_id)
            .limit(5)
            .all()
        )

        arrests = (
            self.db.query(Arrest)
            .filter(Arrest.criminal_id == criminal_id)
            .order_by(Arrest.arrest_date.desc())
            .limit(5)
            .all()
        )

        return {
            "criminal": criminal,
            "gang": gang,
            "linked_firs": linked_firs,
            "associates": associates,
            "arrests": arrests,
        }

