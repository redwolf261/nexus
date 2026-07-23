from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.audit.service import AuditService
from backend.audit.audit_models import (
    AuditEntryDTO, AuditFilterDTO, EventCategory, IntegrityReportDTO, AuditExportRequestDTO
)
from backend.api.dependencies import get_current_user

router = APIRouter(prefix="/api/audit", tags=["Audit Ledger"])


@router.get("/history", response_model=Dict[str, Any])
def get_audit_history(
    event_category: Optional[EventCategory] = None,
    event_type: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    actor_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    request_id: Optional[str] = None,
    session_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    filters = AuditFilterDTO(
        event_category=event_category,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        actor_id=actor_id,
        correlation_id=correlation_id,
        request_id=request_id,
        session_id=session_id,
        page=page,
        page_size=page_size
    )
    items, total = AuditService.get_history(db, filters)
    return {
        "items": [item.model_dump() for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total > 0 else 1
    }


@router.get("/entity/{entity_type}/{entity_id}", response_model=List[Dict[str, Any]])
def get_entity_audit_trail(
    entity_type: str,
    entity_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    filters = AuditFilterDTO(entity_type=entity_type, entity_id=entity_id, page=1, page_size=500)
    items, _ = AuditService.get_history(db, filters)
    return [item.model_dump() for item in items]


@router.get("/correlation/{correlation_id}", response_model=List[Dict[str, Any]])
def get_correlation_audit_trail(
    correlation_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    filters = AuditFilterDTO(correlation_id=correlation_id, page=1, page_size=500)
    items, _ = AuditService.get_history(db, filters)
    return [item.model_dump() for item in items]


@router.get("/request/{request_id}", response_model=List[Dict[str, Any]])
def get_request_audit_trail(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    filters = AuditFilterDTO(request_id=request_id, page=1, page_size=500)
    items, _ = AuditService.get_history(db, filters)
    return [item.model_dump() for item in items]


@router.get("/user/{user_id}", response_model=List[Dict[str, Any]])
def get_user_activity_trail(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    filters = AuditFilterDTO(actor_id=user_id, page=1, page_size=500)
    items, _ = AuditService.get_history(db, filters)
    return [item.model_dump() for item in items]


@router.get("/integrity/verify", response_model=Dict[str, Any])
def verify_audit_ledger_integrity(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    report = AuditService.verify_integrity(db)
    return report.model_dump()


@router.post("/export")
def export_audit_ledger(
    request: AuditExportRequestDTO,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    # RBAC check: only Admin, Supervisor, ACP, DCP permitted to export audit logs
    user_role = current_user.get("role", "ANALYST").upper()
    if user_role not in ["ADMIN", "SUPERVISOR", "ACP", "DCP"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="RBAC authorization failed: Audit export requires SUPERVISOR or ADMIN privileges."
        )

    filters = request.filters or AuditFilterDTO(page=1, page_size=5000)
    filters.page_size = 5000  # Cap export size
    content = AuditService.export_audit_log(db, filters, export_format=request.format)

    media_type = "application/json"
    if request.format.lower() == "csv":
        media_type = "text/csv"
    elif request.format.lower() == "ndjson":
        media_type = "application/x-ndjson"

    filename = f"nexus_audit_export_{request.format.lower()}"
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}.{request.format.lower()}"}
    )
