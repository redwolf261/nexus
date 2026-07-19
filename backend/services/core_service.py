from sqlalchemy.orm import Session
from backend.repositories.postgres_repo import PostgresRepository
from backend.schemas.analytics import OmniSearchResponse, SearchResult

def get_firs_service(db: Session, limit: int = 50):
    repo = PostgresRepository(db)
    return repo.get_firs(limit=limit)

def get_officer_dashboard_service(officer_id: str):
    return {
        "officer_id": officer_id,
        "cases_open": 14,
        "cases_closed": 42,
        "average_delay_days": 12.5,
        "workload": "High",
        "patrol_area": "Koramangala Zone 1"
    }

def get_omni_search_service(query: str, db: Session):
    # Mocking search logic for demo. 
    # In reality, this would hit PostgreSQL Full Text Search or ElasticSearch.
    results = [
        SearchResult(type="FIR", id="FIR-100", name="Robbery at Koramangala", snippet="Matched description: 'stolen vehicle'"),
        SearchResult(type="Person", id="P-123", name=query.capitalize(), snippet="Matched known alias.")
    ]
    return OmniSearchResponse(query=query, results=results)
