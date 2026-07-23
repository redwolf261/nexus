"""API Dependency helpers and re-exports for FastAPI routers."""

from backend.database import get_db
from backend.auth.deps import get_current_user, require_role

__all__ = ["get_db", "get_current_user", "require_role"]
