from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.compliance.compliance_service import ComplianceService
from backend.compliance.risk_engine import RiskEngine
from backend.compliance.monitor import ComplianceMonitor
from backend.compliance.compliance_contracts import (
    ComplianceDashboardDTO, ComplianceViolationDTO, ComplianceRiskDTO,
    ComplianceFilterDTO, ComplianceRuleDTO, ScanRequestDTO, RuleCategory, SeverityLevel
)
from backend.api.dependencies import get_current_user

router = APIRouter(prefix="/api/compliance", tags=["Compliance Monitoring Engine"])


@router.get("/dashboard", response_model=Dict[str, Any])
def get_compliance_dashboard(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    dto = ComplianceService.get_dashboard(db)
    return dto.model_dump()


@router.get("/violations", response_model=Dict[str, Any])
def get_compliance_violations(
    category: Optional[RuleCategory] = None,
    severity: Optional[SeverityLevel] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    actor_id: Optional[str] = None,
    district_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    filters = ComplianceFilterDTO(
        category=category,
        severity=severity,
        entity_type=entity_type,
        entity_id=entity_id,
        actor_id=actor_id,
        district_id=district_id,
        page=page,
        page_size=page_size
    )
    items, total = ComplianceService.get_violations(db, filters)
    return {
        "items": [item.model_dump() for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total > 0 else 1
    }


@router.get("/entity/{entity_id}", response_model=List[Dict[str, Any]])
def get_entity_compliance(
    entity_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    filters = ComplianceFilterDTO(entity_id=entity_id, page=1, page_size=200)
    items, _ = ComplianceService.get_violations(db, filters)
    return [item.model_dump() for item in items]


@router.get("/user/{user_id}", response_model=List[Dict[str, Any]])
def get_user_compliance(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    filters = ComplianceFilterDTO(actor_id=user_id, page=1, page_size=200)
    items, _ = ComplianceService.get_violations(db, filters)
    return [item.model_dump() for item in items]


@router.get("/rules", response_model=List[Dict[str, Any]])
def get_compliance_rules(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    rules = ComplianceService.get_rules(db)
    return [r.model_dump() for r in rules]


@router.post("/scan", response_model=Dict[str, Any])
def trigger_compliance_scan(
    request: ScanRequestDTO,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    if request.scan_scope.upper() == "ENTITY" and request.target_entity_id:
        result = ComplianceMonitor.scan_entity(
            db, request.target_entity_type or "Task", request.target_entity_id
        )
    else:
        result = ComplianceMonitor.scan_incremental(db)

    return {"status": "SUCCESS", "result": result}


@router.post("/recalculate", response_model=Dict[str, Any])
def recalculate_compliance_risk(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    risk_dto = RiskEngine.calculate_risk(db)
    return risk_dto.model_dump()


@router.get("/risk", response_model=Dict[str, Any])
def get_compliance_risk(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    risk_dto = RiskEngine.calculate_risk(db)
    return risk_dto.model_dump()


@router.get("/history", response_model=Dict[str, Any])
def get_compliance_history(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    dto = ComplianceService.get_dashboard(db)
    return {
        "trend_7d": dto.trend_7d,
        "trend_30d": dto.trend_30d,
        "compliance_score": dto.compliance_score
    }


@router.post("/export")
def export_compliance(
    export_format: str = Query("json", alias="format"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    # RBAC check: only ADMIN, SUPERVISOR, ACP, DCP allowed
    user_role = current_user.get("role", "ANALYST").upper()
    if user_role not in ["ADMIN", "SUPERVISOR", "ACP", "DCP"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="RBAC authorization failed: Compliance export requires SUPERVISOR or ADMIN role."
        )

    filters = ComplianceFilterDTO(page=1, page_size=2000)
    content = ComplianceService.export_report(db, filters, export_format=export_format)

    media_type = "application/json"
    if export_format.lower() == "csv":
        media_type = "text/csv"
    elif export_format.lower() == "ndjson":
        media_type = "application/x-ndjson"

    filename = f"nexus_compliance_report_{export_format.lower()}"
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}.{export_format.lower()}"}
    )
