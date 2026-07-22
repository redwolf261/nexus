from sqlalchemy.orm import Session
from backend.db.schema import AuditLog

def log_audit_event(
    db: Session,
    user_id: str,
    action: str,
    target_id: str,
    request_id: str,
    ip_address: str,
    status: str = "SUCCESS"
):
    log_entry = AuditLog(
        user_id=user_id,
        action=action,
        target_id=target_id,
        request_id=request_id,
        ip_address=ip_address,
        status=status
    )
    db.add(log_entry)
    db.commit()
