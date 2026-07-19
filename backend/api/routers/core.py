from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from backend.database import get_db
from backend.schemas.core import FIRResponse, PersonResponse
from backend.schemas.analytics import GraphPersonResponse, OfficerDashboardResponse, OmniSearchResponse
from backend.services.core_service import get_firs_service, get_officer_dashboard_service, get_omni_search_service
from backend.services.analytics_service import get_person_graph_service

router = APIRouter(prefix="/api", tags=["Core"])

@router.get("/search", response_model=OmniSearchResponse)
def search_omni(q: str, db: Session = Depends(get_db)):
    """Global search across FIRs, Persons, Vehicles, Gangs, etc."""
    return get_omni_search_service(q, db)

@router.get("/firs", response_model=List[FIRResponse])
def get_firs(limit: int = 50, db: Session = Depends(get_db)):
    """Retrieve a list of FIRs from PostgreSQL."""
    return get_firs_service(db, limit)

@router.get("/graph/person/{person_id}", response_model=GraphPersonResponse)
def get_person_graph(person_id: str):
    """Retrieve the neighborhood graph and risk score for a specific person."""
    return get_person_graph_service(person_id)

@router.get("/officer/{officer_id}", response_model=OfficerDashboardResponse)
def get_officer_dashboard(officer_id: str):
    """Retrieve dashboard metrics for a specific police officer."""
    return get_officer_dashboard_service(officer_id)
