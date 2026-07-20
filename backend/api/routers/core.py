from __future__ import annotations

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.core import (
    FIRResponse, PersonResponse,
    FIRDetailResponse, PersonDetailResponse, VehicleDetailResponse, CriminalDetailResponse,
    AccusedSummary, VictimSummary, InvLogSummary, VehicleSummary, PhoneSummary,
    CriminalSummary, GangSummary, ArrestSummary,
)
from backend.schemas.analytics import GraphPersonResponse, OfficerDashboardResponse, OmniSearchResponse
from backend.services.core_service import (
    get_firs_service,
    get_officer_dashboard_service,
    get_omni_search_service,
    get_fir_detail_service,
    get_person_detail_service,
    get_vehicle_detail_service,
    get_criminal_detail_service,
)
from backend.services.analytics_service import get_person_graph_service

router = APIRouter(prefix="/api", tags=["Core"])


@router.get("/search", response_model=OmniSearchResponse)
def search_omni(q: str, db: Session = Depends(get_db)):
    """Global search across FIRs, Persons, Vehicles, Criminals."""
    return get_omni_search_service(q, db)


@router.get("/firs", response_model=List[FIRResponse])
def get_firs(
    district_id: Optional[str] = None,
    crime_type: Optional[str] = None,
    crime_category: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    is_gang_crime: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Retrieve filtered FIRs from PostgreSQL."""
    return get_firs_service(
        db,
        limit=limit,
        district_id=district_id,
        crime_type=crime_type,
        crime_category=crime_category,
        status=status,
        date_from=date_from,
        date_to=date_to,
        is_gang_crime=is_gang_crime,
        offset=offset,
    )


@router.get("/graph/person/{person_id}", response_model=GraphPersonResponse)
def get_person_graph(person_id: str):
    """Retrieve the neighbourhood graph and risk score for a specific person."""
    return get_person_graph_service(person_id)


@router.get("/officer/{officer_id}", response_model=OfficerDashboardResponse)
def get_officer_dashboard(officer_id: str, db: Session = Depends(get_db)):
    """Retrieve real case-load metrics for a specific police officer."""
    return get_officer_dashboard_service(officer_id, db)


# ── Entity Detail Endpoints (Investigation Drawer) ────────────────────────────

@router.get("/fir/{fir_id}", response_model=FIRDetailResponse)
def get_fir_detail(fir_id: str, db: Session = Depends(get_db)):
    """Full FIR intelligence package: accused, victims, evidence, inv log, linked assets."""
    raw = get_fir_detail_service(fir_id, db)
    if not raw:
        raise HTTPException(status_code=404, detail=f"FIR {fir_id} not found")
    return FIRDetailResponse(
        fir=FIRResponse.model_validate(raw["fir"]),
        accused=[AccusedSummary.model_validate(a) for a in raw["accused"]],
        victims=[VictimSummary.model_validate(v) for v in raw["victims"]],
        evidence_count=raw["evidence_count"],
        investigation_logs=[InvLogSummary.model_validate(l) for l in raw["investigation_logs"]],
        linked_vehicles=[VehicleSummary.model_validate(v) for v in raw["linked_vehicles"]],
        linked_phones=[PhoneSummary.model_validate(p) for p in raw["linked_phones"]],
    )


@router.get("/person/{person_id}", response_model=PersonDetailResponse)
def get_person_detail(person_id: str, db: Session = Depends(get_db)):
    """Person profile with criminal record, vehicles, phones, gang, and linked FIRs."""
    raw = get_person_detail_service(person_id, db)
    if not raw:
        raise HTTPException(status_code=404, detail=f"Person {person_id} not found")
    return PersonDetailResponse(
        person=PersonResponse.model_validate(raw["person"]),
        criminal=CriminalSummary.model_validate(raw["criminal"]) if raw.get("criminal") else None,
        linked_firs=[FIRResponse.model_validate(f) for f in raw["linked_firs"]],
        vehicles=[VehicleSummary.model_validate(v) for v in raw["vehicles"]],
        phones=[PhoneSummary.model_validate(p) for p in raw["phones"]],
        gang=GangSummary.model_validate(raw["gang"]) if raw.get("gang") else None,
    )


@router.get("/vehicle/{vehicle_id}", response_model=VehicleDetailResponse)
def get_vehicle_detail(vehicle_id: str, db: Session = Depends(get_db)):
    """Vehicle intelligence: owner, registration, stolen flag, and linked FIRs."""
    raw = get_vehicle_detail_service(vehicle_id, db)
    if not raw:
        raise HTTPException(status_code=404, detail=f"Vehicle {vehicle_id} not found")
    return VehicleDetailResponse(
        vehicle=VehicleSummary.model_validate(raw["vehicle"]),
        owner=PersonResponse.model_validate(raw["owner"]) if raw.get("owner") else None,
        linked_firs=[FIRResponse.model_validate(f) for f in raw["linked_firs"]],
    )


@router.get("/criminal/{criminal_id}", response_model=CriminalDetailResponse)
def get_criminal_detail(criminal_id: str, db: Session = Depends(get_db)):
    """Full criminal dossier: gang, MO, associates, arrest history, and FIRs."""
    raw = get_criminal_detail_service(criminal_id, db)
    if not raw:
        raise HTTPException(status_code=404, detail=f"Criminal {criminal_id} not found")
    return CriminalDetailResponse(
        criminal=CriminalSummary.model_validate(raw["criminal"]),
        gang=GangSummary.model_validate(raw["gang"]) if raw.get("gang") else None,
        linked_firs=[FIRResponse.model_validate(f) for f in raw["linked_firs"]],
        associates=[CriminalSummary.model_validate(a) for a in raw["associates"]],
        arrests=[ArrestSummary.model_validate(a) for a in raw["arrests"]],
    )
