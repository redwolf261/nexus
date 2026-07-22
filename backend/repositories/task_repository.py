"""Repository layer for task operations.

Provides data access for investigation tasks, dependencies, and templates.
All operations use SQLAlchemy ORM with optimistic locking on version field.
"""

from typing import List, Optional, Dict, Any
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from backend.db.schema import (
    InvestigationTask, TaskDependency, TaskTemplate, TemplateTask,
    TemplateTaskDependency, TaskStatus, TaskPriority, TaskCategory,
    SLAState, DependencyType, Investigation
)


class TaskRepository:
    """Data access for investigation tasks."""

    def __init__(self, session: Session):
        self.session = session

    def create_task(
        self,
        investigation_id: str,
        title: str,
        description: str,
        category: TaskCategory,
        priority: TaskPriority,
        sla_hours: Optional[int] = None,
        template_task_id: Optional[str] = None,
        parent_task_id: Optional[str] = None,
        assigned_officer_id: Optional[str] = None,
        is_recurring: bool = False,
        recurrence_interval_hours: Optional[int] = None,
    ) -> InvestigationTask:
        """Create a new investigation task.

        Args:
            investigation_id: Parent investigation
            title: Task title
            description: Task description
            category: Task category enum
            priority: Task priority enum
            sla_hours: SLA duration in hours (optional)
            template_task_id: Link to template task (optional)
            parent_task_id: Parent task for subtasks (optional)
            assigned_officer_id: Officer assigned (optional)
            is_recurring: Whether task recurs
            recurrence_interval_hours: Recurrence interval

        Returns:
            Created InvestigationTask instance
        """
        task_id = str(uuid4())
        due_at = None
        if sla_hours:
            due_at = datetime.utcnow() + timedelta(hours=sla_hours)

        task = InvestigationTask(
            id=task_id,
            investigation_id=investigation_id,
            template_task_id=template_task_id,
            parent_task_id=parent_task_id,
            title=title,
            description=description,
            category=category,
            priority=priority,
            status=TaskStatus.CREATED,
            assigned_officer_id=assigned_officer_id,
            created_at=datetime.utcnow(),
            sla_hours=sla_hours,
            due_at=due_at,
            sla_state=SLAState.NORMAL,
            is_recurring=is_recurring,
            recurrence_interval_hours=recurrence_interval_hours,
        )
        self.session.add(task)
        self.session.flush()
        return task

    def get_task(self, task_id: str) -> Optional[InvestigationTask]:
        """Retrieve a task by ID."""
        return self.session.query(InvestigationTask).filter_by(id=task_id).first()

    def update_task(
        self,
        task_id: str,
        expected_version: int,
        **updates
    ) -> InvestigationTask:
        """Update task with optimistic locking.

        Args:
            task_id: Task to update
            expected_version: Current version (for concurrency check)
            **updates: Fields to update

        Returns:
            Updated task

        Raises:
            ValueError: If version mismatch (concurrent modification)
        """
        task = self.session.query(InvestigationTask).filter_by(id=task_id).first()
        if not task:
            raise ValueError(f"Task {task_id} not found")

        if task.version != expected_version:
            raise ValueError(
                f"Concurrent modification detected. "
                f"Expected version {expected_version}, got {task.version}"
            )

        for key, value in updates.items():
            if hasattr(task, key):
                setattr(task, key, value)

        task.version += 1
        task.updated_at = datetime.utcnow() if hasattr(task, 'updated_at') else None
        self.session.flush()
        return task

    def assign_task(self, task_id: str, officer_id: str, expected_version: int) -> InvestigationTask:
        """Assign task to officer.

        Transition: CREATED -> ASSIGNED
        """
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        if task.status != TaskStatus.CREATED:
            raise ValueError(
                f"Cannot assign task in {task.status} status. "
                f"Expected {TaskStatus.CREATED}"
            )

        return self.update_task(
            task_id,
            expected_version,
            assigned_officer_id=officer_id,
            status=TaskStatus.ASSIGNED,
            assigned_at=datetime.utcnow(),
        )

    def start_task(self, task_id: str, expected_version: int) -> InvestigationTask:
        """Start task (begin work).

        Transition: ASSIGNED -> ACTIVE
        Also checks all dependencies are satisfied.
        """
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        if task.status != TaskStatus.ASSIGNED:
            raise ValueError(
                f"Cannot start task in {task.status} status. "
                f"Expected {TaskStatus.ASSIGNED}"
            )

        # Check dependencies
        dep_repo = DependencyRepository(self.session)
        unmet = dep_repo.find_unmet_dependencies(task_id)
        if unmet:
            dep_ids = ", ".join([d.depends_on_task_id for d in unmet])
            raise ValueError(
                f"Cannot start task. Unmet dependencies: {dep_ids}"
            )

        return self.update_task(
            task_id,
            expected_version,
            status=TaskStatus.ACTIVE,
            started_at=datetime.utcnow(),
        )

    def complete_task(self, task_id: str, expected_version: int) -> InvestigationTask:
        """Mark task as complete.

        Transition: ACTIVE -> COMPLETED
        Also triggers recurring task creation if applicable.
        """
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        if task.status != TaskStatus.ACTIVE:
            raise ValueError(
                f"Cannot complete task in {task.status} status. "
                f"Expected {TaskStatus.ACTIVE}"
            )

        updated_task = self.update_task(
            task_id,
            expected_version,
            status=TaskStatus.COMPLETED,
            completed_at=datetime.utcnow(),
        )

        # Handle recurring tasks
        if updated_task.is_recurring and updated_task.recurrence_interval_hours:
            next_due = datetime.utcnow() + timedelta(
                hours=updated_task.recurrence_interval_hours
            )
            self.create_task(
                investigation_id=updated_task.investigation_id,
                title=updated_task.title,
                description=updated_task.description,
                category=updated_task.category,
                priority=updated_task.priority,
                sla_hours=updated_task.sla_hours,
                template_task_id=updated_task.template_task_id,
                assigned_officer_id=updated_task.assigned_officer_id,
                is_recurring=True,
                recurrence_interval_hours=updated_task.recurrence_interval_hours,
            )

        return updated_task

    def cancel_task(self, task_id: str, expected_version: int, reason: str = "") -> InvestigationTask:
        """Cancel task.

        Transition: CREATED/ASSIGNED/ACTIVE -> CANCELLED
        Terminal states (COMPLETED, CANCELLED, SKIPPED) cannot be cancelled (Finding 1 fix)
        """
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        # Fix Finding 1: SKIPPED is terminal and cannot transition
        if task.status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED, TaskStatus.SKIPPED]:
            raise ValueError(
                f"Cannot cancel task in {task.status} status"
            )

        return self.update_task(
            task_id,
            expected_version,
            status=TaskStatus.CANCELLED,
        )

    def skip_task(self, task_id: str, expected_version: int) -> InvestigationTask:
        """Skip task (mark as not applicable).

        Transition: ASSIGNED/ACTIVE -> SKIPPED
        """
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        if task.status not in [TaskStatus.ASSIGNED, TaskStatus.ACTIVE]:
            raise ValueError(
                f"Cannot skip task in {task.status} status"
            )

        return self.update_task(
            task_id,
            expected_version,
            status=TaskStatus.SKIPPED,
        )

    def block_task(self, task_id: str, expected_version: int, reason: str = "") -> InvestigationTask:
        """Block task (waiting for external input).

        Transition: ACTIVE -> BLOCKED
        Finding 8 fix: Record when task entered BLOCKED state to pause SLA
        """
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        if task.status != TaskStatus.ACTIVE:
            raise ValueError(
                f"Cannot block task in {task.status} status. "
                f"Expected {TaskStatus.ACTIVE}"
            )

        return self.update_task(
            task_id,
            expected_version,
            status=TaskStatus.BLOCKED,
            blocked_at=datetime.utcnow(),  # Record when blocked for SLA pause
        )

    def unblock_task(self, task_id: str, expected_version: int) -> InvestigationTask:
        """Resume blocked task.

        Transition: BLOCKED -> ACTIVE
        Finding 8 fix: Extend SLA deadline by the time task was blocked
        """
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        if task.status != TaskStatus.BLOCKED:
            raise ValueError(
                f"Cannot unblock task in {task.status} status. "
                f"Expected {TaskStatus.BLOCKED}"
            )

        # Extend SLA deadline by blocked duration
        updates = {"status": TaskStatus.ACTIVE, "blocked_at": None}
        if task.blocked_at and task.due_at:
            blocked_duration = datetime.utcnow() - task.blocked_at
            task.due_at += blocked_duration
            task.total_blocked_seconds += int(blocked_duration.total_seconds())
            updates["due_at"] = task.due_at
            updates["total_blocked_seconds"] = task.total_blocked_seconds

        return self.update_task(task_id, expected_version, **updates)

    def list_tasks_by_investigation(
        self,
        investigation_id: str,
        status: Optional[TaskStatus] = None,
        include_completed: bool = False,
    ) -> List[InvestigationTask]:
        """List all tasks for an investigation."""
        query = self.session.query(InvestigationTask).filter_by(
            investigation_id=investigation_id
        )

        if status:
            query = query.filter_by(status=status)
        elif not include_completed:
            query = query.filter(
                InvestigationTask.status.notin_([TaskStatus.COMPLETED, TaskStatus.CANCELLED])
            )

        return query.order_by(InvestigationTask.created_at).all()

    def list_tasks_by_officer(
        self,
        officer_id: str,
        status: Optional[TaskStatus] = None,
    ) -> List[InvestigationTask]:
        """List all tasks assigned to an officer."""
        query = self.session.query(InvestigationTask).filter_by(
            assigned_officer_id=officer_id
        )

        if status:
            query = query.filter_by(status=status)
        else:
            query = query.filter(
                InvestigationTask.status.notin_([TaskStatus.COMPLETED, TaskStatus.CANCELLED])
            )

        return query.order_by(InvestigationTask.due_at).all()

    def find_overdue_tasks(self, hours_before_due: int = 4) -> List[InvestigationTask]:
        """Find tasks approaching or exceeding SLA.

        Returns tasks where due_at is within next X hours or already passed.
        """
        threshold = datetime.utcnow() + timedelta(hours=hours_before_due)
        return self.session.query(InvestigationTask).filter(
            and_(
                InvestigationTask.due_at <= threshold,
                InvestigationTask.status.notin_([TaskStatus.COMPLETED, TaskStatus.CANCELLED]),
            )
        ).order_by(InvestigationTask.due_at).all()

    def find_blocked_tasks(self) -> List[InvestigationTask]:
        """Find all blocked tasks (waiting for input)."""
        return self.session.query(InvestigationTask).filter_by(
            status=TaskStatus.BLOCKED
        ).order_by(InvestigationTask.created_at).all()

    def update_sla_states(self) -> Dict[str, int]:
        """Update SLA states for all open tasks.

        Returns counts: {normal, warning, breached}
        """
        now = datetime.utcnow()
        counts = {"normal": 0, "warning": 0, "breached": 0}

        open_tasks = self.session.query(InvestigationTask).filter(
            InvestigationTask.status.notin_([TaskStatus.COMPLETED, TaskStatus.CANCELLED]),
            InvestigationTask.due_at.isnot(None),
        ).all()

        for task in open_tasks:
            if task.due_at <= now:
                state = SLAState.BREACHED
                counts["breached"] += 1
            elif task.due_at <= now + timedelta(hours=4):
                state = SLAState.WARNING
                counts["warning"] += 1
            else:
                state = SLAState.NORMAL
                counts["normal"] += 1

            if task.sla_state != state:
                task.sla_state = state
                task.version += 1

        self.session.flush()
        return counts


class DependencyRepository:
    """Data access for task dependencies."""

    def __init__(self, session: Session):
        self.session = session

    def create_dependency(
        self,
        task_id: str,
        depends_on_task_id: str,
        dependency_type: DependencyType = DependencyType.FINISH_TO_START,
    ) -> TaskDependency:
        """Create a task dependency.

        Args:
            task_id: Task that depends
            depends_on_task_id: Task that must complete first
            dependency_type: Type of dependency

        Raises:
            ValueError: If circular dependency detected
        """
        # Check for circular dependency
        if self._would_create_cycle(task_id, depends_on_task_id):
            raise ValueError(
                f"Creating dependency {task_id} -> {depends_on_task_id} "
                f"would create a circular dependency"
            )

        dep_id = str(uuid4())
        dep = TaskDependency(
            id=dep_id,
            task_id=task_id,
            depends_on_task_id=depends_on_task_id,
            dependency_type=dependency_type,
            created_at=datetime.utcnow(),
        )
        self.session.add(dep)
        self.session.flush()
        return dep

    def find_unmet_dependencies(self, task_id: str) -> List[TaskDependency]:
        """Find dependencies that haven't been satisfied yet.

        Returns all dependencies of task_id where depends_on_task is not COMPLETED.
        """
        return self.session.query(TaskDependency).filter(
            and_(
                TaskDependency.task_id == task_id,
                TaskDependency.dependency_type == DependencyType.FINISH_TO_START,
            )
        ).join(
            InvestigationTask,
            TaskDependency.depends_on_task_id == InvestigationTask.id,
        ).filter(
            InvestigationTask.status != TaskStatus.COMPLETED,
        ).all()

    def find_dependents(self, task_id: str) -> List[TaskDependency]:
        """Find all tasks that depend on this task."""
        return self.session.query(TaskDependency).filter_by(
            depends_on_task_id=task_id,
            dependency_type=DependencyType.FINISH_TO_START,
        ).all()

    def _would_create_cycle(self, task_id: str, depends_on_task_id: str) -> bool:
        """Check if creating this dependency would create a cycle (DFS).

        Fix Finding 2: Correct DFS direction to follow dependencies forward, not backward.
        To detect cycle for (task_id → depends_on_task_id):
        - Start from depends_on_task_id
        - Follow forward dependencies (what depends_on_task_id depends on)
        - If we reach task_id, a cycle exists
        """
        visited = set()
        stack = [depends_on_task_id]

        while stack:
            current = stack.pop()
            if current == task_id:
                return True  # Cycle detected
            if current in visited:
                continue
            visited.add(current)

            # Find all tasks that CURRENT depends on (forward direction, not backward)
            # Query: where task_id=current (current's dependencies)
            dependencies = self.session.query(TaskDependency).filter_by(
                task_id=current
            ).all()
            for dep in dependencies:
                if dep.depends_on_task_id not in visited:
                    stack.append(dep.depends_on_task_id)

        return False

    def list_dependencies(self, task_id: str) -> List[TaskDependency]:
        """List all dependencies for a task."""
        return self.session.query(TaskDependency).filter_by(
            task_id=task_id
        ).all()

    def delete_dependency(self, task_id: str, depends_on_task_id: str) -> bool:
        """Delete a specific dependency."""
        result = self.session.query(TaskDependency).filter(
            and_(
                TaskDependency.task_id == task_id,
                TaskDependency.depends_on_task_id == depends_on_task_id,
            )
        ).delete()
        self.session.flush()
        return result > 0


class TaskTemplateRepository:
    """Data access for task templates."""

    def __init__(self, session: Session):
        self.session = session

    def create_template(
        self,
        name: str,
        case_type: str,
        description: str = "",
    ) -> TaskTemplate:
        """Create a new task template."""
        template_id = str(uuid4())
        template = TaskTemplate(
            id=template_id,
            name=name,
            case_type=case_type,
            description=description,
            active=True,
            created_at=datetime.utcnow(),
        )
        self.session.add(template)
        self.session.flush()
        return template

    def get_template(self, template_id: str) -> Optional[TaskTemplate]:
        """Retrieve a template by ID."""
        return self.session.query(TaskTemplate).filter_by(id=template_id).first()

    def get_template_by_case_type(self, case_type: str) -> Optional[TaskTemplate]:
        """Get the active template for a case type."""
        return self.session.query(TaskTemplate).filter(
            and_(
                TaskTemplate.case_type == case_type,
                TaskTemplate.active == True,
            )
        ).first()

    def list_templates(self, active_only: bool = True) -> List[TaskTemplate]:
        """List all templates."""
        query = self.session.query(TaskTemplate)
        if active_only:
            query = query.filter_by(active=True)
        return query.order_by(TaskTemplate.name).all()

    def instantiate_template(
        self,
        template_id: str,
        investigation_id: str,
        assigned_officer_id: Optional[str] = None,
    ) -> List[InvestigationTask]:
        """Create task instances from template.

        Creates all template tasks and wires up their dependencies.

        Returns list of created tasks.
        """
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

        task_repo = TaskRepository(self.session)
        dep_repo = DependencyRepository(self.session)

        # Get all template tasks, ordered
        template_tasks = self.session.query(TemplateTask).filter_by(
            template_id=template_id
        ).order_by(TemplateTask.order).all()

        # Map template task ID -> created task ID
        created_tasks = {}

        for tt in template_tasks:
            task = task_repo.create_task(
                investigation_id=investigation_id,
                title=tt.title,
                description=tt.description,
                category=tt.category,
                priority=tt.priority,
                sla_hours=tt.sla_hours,
                template_task_id=tt.id,
                assigned_officer_id=assigned_officer_id,
                is_recurring=tt.is_recurring,
                recurrence_interval_hours=tt.recurrence_interval_hours,
            )
            created_tasks[tt.id] = task

        # Wire up dependencies
        template_deps = self.session.query(TemplateTaskDependency).filter(
            TemplateTaskDependency.task_id.in_(created_tasks.keys())
        ).all()

        for template_dep in template_deps:
            if template_dep.depends_on_task_id in created_tasks:
                dep_repo.create_dependency(
                    created_tasks[template_dep.task_id].id,
                    created_tasks[template_dep.depends_on_task_id].id,
                    template_dep.dependency_type,
                )

        return list(created_tasks.values())

    def add_template_task(
        self,
        template_id: str,
        order: int,
        title: str,
        description: str,
        category: TaskCategory,
        priority: TaskPriority,
        sla_hours: Optional[int] = None,
        is_recurring: bool = False,
        recurrence_interval_hours: Optional[int] = None,
    ) -> TemplateTask:
        """Add a task to a template."""
        task_id = str(uuid4())
        task = TemplateTask(
            id=task_id,
            template_id=template_id,
            order=order,
            title=title,
            description=description,
            category=category,
            priority=priority,
            sla_hours=sla_hours,
            is_recurring=is_recurring,
            recurrence_interval_hours=recurrence_interval_hours,
            created_at=datetime.utcnow(),
        )
        self.session.add(task)
        self.session.flush()
        return task

    def add_template_dependency(
        self,
        template_id: str,
        task_id: str,
        depends_on_task_id: str,
        dependency_type: DependencyType = DependencyType.FINISH_TO_START,
    ) -> TemplateTaskDependency:
        """Add a dependency between template tasks."""
        dep_id = str(uuid4())
        dep = TemplateTaskDependency(
            id=dep_id,
            task_id=task_id,
            depends_on_task_id=depends_on_task_id,
            dependency_type=dependency_type,
            created_at=datetime.utcnow(),
        )
        self.session.add(dep)
        self.session.flush()
        return dep
