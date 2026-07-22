from __future__ import annotations

from sqlalchemy.orm import Session

from backend.repositories.postgres_repo import PostgresRepository
from backend.schemas.analytics import OmniSearchResponse, SearchResult


def get_firs_service(db: Session, limit: int = 50, **filters):
    repo = PostgresRepository(db)
    return repo.get_firs(limit=limit, **filters)


def get_officer_dashboard_service(officer_id: str, db: Session):
    repo = PostgresRepository(db)
    stats = repo.get_officer_stats(officer_id)
    if not stats:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Officer not found")
    return stats


def get_omni_search_service(query: str, db: Session):
    repo = PostgresRepository(db)
    raw = repo.search(query, limit=20)
    results = [
        SearchResult(
            type=r["type"],
            id=r["id"],
            name=r["name"],
            snippet=r["snippet"],
        )
        for r in raw
    ]
    return OmniSearchResponse(query=query, results=results)


# ── Entity Detail Services (Investigation Drawer) ─────────────────────────────

def get_fir_detail_service(fir_id: str, db: Session):
    """Return full FIR detail dict — serialized by router."""
    repo = PostgresRepository(db)
    return repo.get_fir_full(fir_id)


def get_person_detail_service(person_id: str, db: Session):
    """Return person profile + criminal record + linked FIRs."""
    repo = PostgresRepository(db)
    return repo.get_person_full(person_id)


def get_vehicle_detail_service(vehicle_id: str, db: Session):
    """Return vehicle + owner + linked FIRs."""
    repo = PostgresRepository(db)
    return repo.get_vehicle_full(vehicle_id)


def get_criminal_detail_service(criminal_id: str, db: Session):
    """Return full criminal profile."""
    repo = PostgresRepository(db)
    return repo.get_criminal_full(criminal_id)
