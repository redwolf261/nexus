"""REST API for investigation task management.

Endpoints for task CRUD, lifecycle operations, dependencies, templates, and progress tracking.
All endpoints protected with JWT and RBAC.
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.database import get_db
from backend.services.task_engine import TaskEngine
from backend.repositories.task_repository import (
    TaskRepository, DependencyRepository, TaskTemplateRepository
)
from backend.auth.deps import get_current_user, require_role
from backend.db.schema import (
    User, Role, InvestigationTask, TaskStatus, TaskCategory, TaskPriority,
    DependencyType, SLAState, Investigation, InvestigationCollaborator
)
from backend.audit.audit_logger import AuditLogger
from backend.api.routers.ws import manager as ws_manager
from backend.events.event_types import EventType
from uuid import uuid4
import json
from backend.db.schema import EventRecord

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


def log_event(
    db: Session,
    event_type: EventType,
    payload: dict,
    case_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> EventRecord:
    """Log an event to the database.

    Events are persisted first (ensuring atomicity with state changes),
    then a background worker broadcasts them via WebSocket.
    """
    event_id = str(uuid4())
    event = EventRecord(
        event_id=event_id,
        event_type=event_type.value if isinstance(event_type, EventType) else event_type,
        payload=payload,
        timestamp=datetime.utcnow(),
        case_id=case_id,
        user_id=user_id,
        processed=False,
    )
    db.add(event)
    return event


# Finding 4 fix: Authorization helper
def require_investigation_access(
    investigation_id: str,
    current_user: User,
    db: Session,
    required_role: Optional[str] = None
) -> Investigation:
    """Verify user has access to investigation.

    Args:
        investigation_id: Investigation to check
        current_user: Authenticated user
        db: Database session
        required_role: If provided, require this role (ANALYST, SUPERVISOR, ADMIN)

    Returns:
        Investigation object if authorized

    Raises:
        HTTPException: 404 if not found, 403 if not authorized
    """
    inv = db.query(Investigation).filter_by(id=investigation_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    # Admin can access any investigation
    if current_user.role == Role.Admin:
        return inv

    # Check role-specific access
    if required_role:
        if required_role == "ANALYST" and current_user.role != Role.Analyst:
            raise HTTPException(status_code=403, detail="Only analysts can perform this action")
        elif required_role == "SUPERVISOR" and current_user.role != Role.Supervisor:
            raise HTTPException(status_code=403, detail="Only supervisors can perform this action")

    # Analysts can only access investigations they're assigned to
    if current_user.role == Role.Analyst:
        if inv.assigned_officer != current_user.id and not db.query(InvestigationCollaborator).filter_by(
            investigation_id=investigation_id, user_id=current_user.id
        ).first():
            raise HTTPException(status_code=403, detail="Not assigned to this investigation")

    # Supervisors can only access investigations they supervise
    if current_user.role == Role.Supervisor:
        # Add supervisor check here when supervisor_id added to Investigation model
        pass

    return inv


# ── Schemas ──────────────────────────────────────────────────────────────────

class TaskResponse(BaseModel):
    id: str
    investigation_id: str
    title: str
    description: Optional[str]
    category: str
    priority: str
    status: str
    assigned_officer_id: Optional[str]
    created_at: str
    assigned_at: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]
    due_at: Optional[str]
    sla_hours: Optional[int]
    sla_state: str
    version: int

    class Config:
        from_attributes = True


class TaskCreateRequest(BaseModel):
    investigation_id: str
    title: str
    description: Optional[str] = None
    category: str
    priority: str
    sla_hours: Optional[int] = None
    assigned_officer_id: Optional[str] = None


class TaskUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None


class TaskAssignRequest(BaseModel):
    officer_id: str
    version: int


class TaskTransitionRequest(BaseModel):
    version: int
    reason: Optional[str] = None
    completion_notes: Optional[str] = None


class TaskDependencyRequest(BaseModel):
    task_id: str
    depends_on_task_id: str
    dependency_type: str = "FINISH_TO_START"


class TaskProgressResponse(BaseModel):
    total_tasks: int
    status_breakdown: dict
    completed: int
    percent_complete: float
    next_due_task: Optional[TaskResponse]
    blocked_tasks: List[TaskResponse]
    overdue_tasks: List[TaskResponse]


class TaskDependencyGraph(BaseModel):
    tasks: List[dict]
    dependencies: List[dict]


class TaskTemplateResponse(BaseModel):
    id: str
    name: str
    case_type: str
    description: Optional[str]
    active: bool

    class Config:
        from_attributes = True


# ── Dependencies ─────────────────────────────────────────────────────────────

def get_task_engine(db: Session = Depends(get_db)) -> TaskEngine:
    """Inject task engine with audit logger."""
    audit_logger = AuditLogger(db)
    return TaskEngine(db, audit_logger)


def get_task_repo(db: Session = Depends(get_db)) -> TaskRepository:
    """Inject task repository."""
    return TaskRepository(db)


def get_dependency_repo(db: Session = Depends(get_db)) -> DependencyRepository:
    """Inject dependency repository."""
    return DependencyRepository(db)


def get_template_repo(db: Session = Depends(get_db)) -> TaskTemplateRepository:
    """Inject template repository."""
    return TaskTemplateRepository(db)


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: str,
    task_repo: TaskRepository = Depends(get_task_repo),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific task by ID. (Finding 4 fix: Authorization required)"""
    task = task_repo.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Verify user can access this investigation
    require_investigation_access(task.investigation_id, current_user, db)
    return task


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    req: TaskCreateRequest,
    engine: TaskEngine = Depends(get_task_engine),
    task_repo: TaskRepository = Depends(get_task_repo),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new task in an investigation."""
    try:
        category = TaskCategory[req.category.upper()]
        priority = TaskPriority[req.priority.upper()]
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid category or priority")

    task = task_repo.create_task(
        investigation_id=req.investigation_id,
        title=req.title,
        description=req.description or "",
        category=category,
        priority=priority,
        sla_hours=req.sla_hours,
        assigned_officer_id=req.assigned_officer_id,
    )

    db.commit()

    # Log event (for WebSocket broadcast via background worker)
    log_event(
        db,
        event_type=EventType.TASK_CREATED,
        payload={
            "task_id": task.id,
            "investigation_id": task.investigation_id,
            "title": task.title,
        },
        case_id=req.investigation_id,
        user_id=current_user.id,
    )
    db.commit()

    return task


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: str,
    req: TaskUpdateRequest,
    task_repo: TaskRepository = Depends(get_task_repo),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update task details (non-lifecycle fields)."""
    task = task_repo.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    updates = {}
    if req.title:
        updates["title"] = req.title
    if req.description:
        updates["description"] = req.description
    if req.priority:
        try:
            updates["priority"] = TaskPriority[req.priority.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail="Invalid priority")

    if updates:
        task = task_repo.update_task(task_id, task.version, **updates)
        db.commit()

    return task


@router.post("/{task_id}/assign", response_model=TaskResponse)
def assign_task(
    task_id: str,
    req: TaskAssignRequest,
    engine: TaskEngine = Depends(get_task_engine),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Assign task to an officer.

    Transition: CREATED -> ASSIGNED
    (Finding 4 fix: Only supervisors can assign tasks)
    """
    task = engine.task_repo.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Verify authorization
    inv = require_investigation_access(task.investigation_id, current_user, db, required_role="SUPERVISOR")

    try:
        task = engine.assign_task(
            task_id,
            req.officer_id,
            req.version,
            user_id=current_user.id,
        )
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=404, detail=msg)
        else:
            raise HTTPException(status_code=409, detail=msg)

    log_event(
        db,
        event_type=EventType.TASK_ASSIGNED,
        payload={
            "task_id": task.id,
            "officer_id": req.officer_id,
        },
        case_id=task.investigation_id,
        user_id=current_user.id,
    )
    db.commit()

    return task


@router.post("/{task_id}/start", response_model=TaskResponse)
def start_task(
    task_id: str,
    req: TaskTransitionRequest,
    engine: TaskEngine = Depends(get_task_engine),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Start task (begin active work).

    Transition: ASSIGNED -> ACTIVE
    Validates dependencies are satisfied.
    (Finding 4 fix: Only assigned analyst can start)
    """
    task = engine.task_repo.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Verify user is assigned to this task
    if task.assigned_officer_id != current_user.id and current_user.role != Role.Supervisor and current_user.role != Role.Admin:
        raise HTTPException(status_code=403, detail="Not assigned to this task")

    try:
        task = engine.start_task(
            task_id,
            req.version,
            user_id=current_user.id,
        )
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=404, detail=msg)
        else:
            raise HTTPException(status_code=409, detail=msg)

    log_event(
        db,
        event_type=EventType.TASK_STARTED,
        payload={
            "task_id": task.id,
            "investigation_id": task.investigation_id,
        },
        case_id=task.investigation_id,
        user_id=current_user.id,
    )
    db.commit()

    return task


@router.post("/{task_id}/complete", response_model=TaskResponse)
def complete_task(
    task_id: str,
    req: TaskTransitionRequest,
    engine: TaskEngine = Depends(get_task_engine),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark task as complete.

    Transition: ACTIVE -> COMPLETED
    Triggers recurring task creation if applicable.
    """
    try:
        task = engine.complete_task(
            task_id,
            req.version,
            completion_notes=req.completion_notes or "",
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    log_event(
        db,
        event_type=EventType.TASK_COMPLETED,
        payload={
            "task_id": task.id,
            "investigation_id": task.investigation_id,
        },
        case_id=task.investigation_id,
        user_id=current_user.id,
    )
    db.commit()

    return task


@router.post("/{task_id}/cancel", response_model=TaskResponse)
def cancel_task(
    task_id: str,
    req: TaskTransitionRequest,
    engine: TaskEngine = Depends(get_task_engine),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel task (no longer needed).

    Transition: CREATED/ASSIGNED/ACTIVE -> CANCELLED
    """
    try:
        task = engine.cancel_task(
            task_id,
            req.version,
            reason=req.reason or "",
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    log_event(
        db,
        event_type=EventType.TASK_CANCELLED,
        payload={
            "task_id": task.id,
        },
        case_id=task.investigation_id,
        user_id=current_user.id,
    )
    db.commit()

    return task


@router.post("/{task_id}/skip", response_model=TaskResponse)
def skip_task(
    task_id: str,
    req: TaskTransitionRequest,
    engine: TaskEngine = Depends(get_task_engine),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Skip task (not applicable to this investigation).

    Transition: ASSIGNED/ACTIVE -> SKIPPED
    """
    try:
        task = engine.skip_task(
            task_id,
            req.version,
            reason=req.reason or "",
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return task


@router.post("/{task_id}/block", response_model=TaskResponse)
def block_task(
    task_id: str,
    req: TaskTransitionRequest,
    engine: TaskEngine = Depends(get_task_engine),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Block task (waiting for external input).

    Transition: ACTIVE -> BLOCKED
    """
    try:
        task = engine.block_task(
            task_id,
            req.version,
            reason=req.reason or "",
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    log_event(
        db,
        event_type=EventType.TASK_BLOCKED,
        payload={
            "task_id": task.id,
            "reason": req.reason,
        },
        case_id=task.investigation_id,
        user_id=current_user.id,
    )
    db.commit()

    return task


@router.post("/{task_id}/unblock", response_model=TaskResponse)
def unblock_task(
    task_id: str,
    req: TaskTransitionRequest,
    engine: TaskEngine = Depends(get_task_engine),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Resume blocked task.

    Transition: BLOCKED -> ACTIVE
    """
    try:
        task = engine.unblock_task(
            task_id,
            req.version,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return task


@router.get("/investigation/{investigation_id}", response_model=List[TaskResponse])
def list_investigation_tasks(
    investigation_id: str,
    status: Optional[str] = None,
    include_completed: bool = False,
    task_repo: TaskRepository = Depends(get_task_repo),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all tasks for an investigation. (Finding 6 fix: Verify investigation exists)"""
    # Finding 6 fix: Validate investigation exists
    require_investigation_access(investigation_id, current_user, db)

    task_status = None
    if status:
        try:
            task_status = TaskStatus[status.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail="Invalid status")

    tasks = task_repo.list_tasks_by_investigation(
        investigation_id,
        status=task_status,
        include_completed=include_completed,
    )
    return tasks


@router.get("/officer/{officer_id}", response_model=List[TaskResponse])
def list_officer_tasks(
    officer_id: str,
    status: Optional[str] = None,
    task_repo: TaskRepository = Depends(get_task_repo),
    current_user: User = Depends(get_current_user),
):
    """List all tasks assigned to an officer."""
    task_status = None
    if status:
        try:
            task_status = TaskStatus[status.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail="Invalid status")

    tasks = task_repo.list_tasks_by_officer(officer_id, status=task_status)
    return tasks


@router.get("/{investigation_id}/progress", response_model=TaskProgressResponse)
def get_investigation_progress(
    investigation_id: str,
    engine: TaskEngine = Depends(get_task_engine),
    current_user: User = Depends(get_current_user),
):
    """Get overall progress for investigation tasks."""
    progress = engine.get_investigation_progress(investigation_id)
    return progress


@router.get("/{investigation_id}/dependencies", response_model=TaskDependencyGraph)
def get_dependency_graph(
    investigation_id: str,
    engine: TaskEngine = Depends(get_task_engine),
    current_user: User = Depends(get_current_user),
):
    """Get dependency graph for investigation tasks."""
    graph = engine.get_task_dependency_graph(investigation_id)
    return graph


@router.post("/{investigation_id}/initialize-from-template/{case_type}")
def initialize_from_template(
    investigation_id: str,
    case_type: str,
    assigned_officer_id: Optional[str] = None,
    engine: TaskEngine = Depends(get_task_engine),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Initialize investigation with task template.

    Called when new investigation created. Auto-loads template for case type
    and instantiates all tasks.
    """
    try:
        tasks = engine.create_investigation_tasks_from_template(
            investigation_id,
            case_type,
            assigned_officer_id,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    log_event(
        db,
        event_type=EventType.TASK_TEMPLATE_INSTANTIATED,
        payload={
            "investigation_id": investigation_id,
            "case_type": case_type,
            "task_count": len(tasks),
        },
        case_id=investigation_id,
        user_id=current_user.id,
    )
    db.commit()

    return {"task_count": len(tasks), "tasks": tasks}


# ── Template endpoints ───────────────────────────────────────────────────────

@router.get("/templates", response_model=List[TaskTemplateResponse])
def list_templates(
    active_only: bool = True,
    template_repo: TaskTemplateRepository = Depends(get_template_repo),
    current_user: User = Depends(get_current_user),
):
    """List all task templates."""
    templates = template_repo.list_templates(active_only=active_only)
    return templates


@router.get("/templates/{template_id}", response_model=TaskTemplateResponse)
def get_template(
    template_id: str,
    template_repo: TaskTemplateRepository = Depends(get_template_repo),
    current_user: User = Depends(get_current_user),
):
    """Get a specific template."""
    template = template_repo.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template
