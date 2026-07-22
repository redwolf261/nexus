"""Task engine service — operational workflow orchestration.

Manages task lifecycle, validates transitions, enforces dependencies,
handles recurring tasks, and maintains SLA tracking.

All operations are transactional through SQLAlchemy session.
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging

from backend.db.schema import (
    InvestigationTask, TaskDependency, TaskTemplate, TemplateTask,
    TaskStatus, TaskCategory, TaskPriority, SLAState, DependencyType
)
from backend.repositories.task_repository import (
    TaskRepository, DependencyRepository, TaskTemplateRepository
)
from backend.audit import AuditLogger

logger = logging.getLogger(__name__)


class TaskEngine:
    """Orchestration layer for investigation task workflows."""

    def __init__(self, session: Session, audit_logger: AuditLogger):
        self.session = session
        self.audit_logger = audit_logger
        self.task_repo = TaskRepository(session)
        self.dep_repo = DependencyRepository(session)
        self.template_repo = TaskTemplateRepository(session)

    def create_investigation_tasks_from_template(
        self,
        investigation_id: str,
        case_type: str,
        assigned_officer_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> List[InvestigationTask]:
        """Initialize investigation with task template.

        Called when new investigation is created. Auto-loads matching template
        and instantiates all tasks with dependencies.

        Args:
            investigation_id: Investigation to initialize
            case_type: Investigation case type (used to find template)
            assigned_officer_id: Primary investigating officer
            user_id: User creating investigation (for audit)

        Returns:
            List of created tasks

        Raises:
            ValueError: If no template found for case type
        """
        template = self.template_repo.get_template_by_case_type(case_type)
        if not template:
            raise ValueError(
                f"No active template found for case type {case_type}"
            )

        try:
            tasks = self.template_repo.instantiate_template(
                template.id,
                investigation_id,
                assigned_officer_id,
            )

            # Audit
            self.audit_logger.log(
                user_id=user_id,
                action="TASK_TEMPLATE_INSTANTIATED",
                target_id=investigation_id,
                details={
                    "template_id": template.id,
                    "case_type": case_type,
                    "task_count": len(tasks),
                },
            )

            self.session.commit()
            return tasks

        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to instantiate template: {e}")
            raise

    def assign_task(
        self,
        task_id: str,
        officer_id: str,
        expected_version: int,
        user_id: Optional[str] = None,
    ) -> InvestigationTask:
        """Assign task to officer.

        Transition: CREATED -> ASSIGNED

        Args:
            task_id: Task to assign
            officer_id: Officer to assign to
            expected_version: Current version (concurrency check)
            user_id: User making assignment (for audit)

        Returns:
            Updated task

        Raises:
            ValueError: If invalid transition or version mismatch
        """
        try:
            task = self.task_repo.assign_task(task_id, officer_id, expected_version)

            self.audit_logger.log(
                user_id=user_id,
                action="TASK_ASSIGNED",
                target_id=task_id,
                details={"officer_id": officer_id, "version": task.version},
            )

            self.session.commit()
            return task

        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to assign task: {e}")
            raise

    def start_task(
        self,
        task_id: str,
        expected_version: int,
        user_id: Optional[str] = None,
    ) -> InvestigationTask:
        """Start task (begin active work).

        Transition: ASSIGNED -> ACTIVE

        Validates all dependencies are satisfied before allowing transition.

        Args:
            task_id: Task to start
            expected_version: Current version (concurrency check)
            user_id: Officer starting work (for audit)

        Returns:
            Updated task

        Raises:
            ValueError: If dependencies not met, invalid status, or version mismatch
        """
        try:
            task = self.task_repo.start_task(task_id, expected_version)

            self.audit_logger.log(
                user_id=user_id,
                action="TASK_STARTED",
                target_id=task_id,
                details={"version": task.version},
            )

            self.session.commit()
            return task

        except ValueError as e:
            self.session.rollback()
            logger.warning(f"Cannot start task {task_id}: {e}")
            raise

        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to start task: {e}")
            raise

    def complete_task(
        self,
        task_id: str,
        expected_version: int,
        completion_notes: str = "",
        user_id: Optional[str] = None,
    ) -> InvestigationTask:
        """Mark task complete.

        Transition: ACTIVE -> COMPLETED

        Triggers:
        - Recurring task creation (if applicable)
        - Unblocking of dependent tasks
        - Investigation completion check

        Args:
            task_id: Task to complete
            expected_version: Current version (concurrency check)
            completion_notes: Optional notes on completion
            user_id: Officer completing (for audit)

        Returns:
            Updated task

        Raises:
            ValueError: If invalid status or version mismatch
        """
        try:
            task = self.task_repo.complete_task(task_id, expected_version)

            # Unblock any tasks waiting on this one (Finding 3 fix)
            # Transition all dependent tasks whose dependencies are now satisfied
            dependents = self.dep_repo.find_dependents(task_id)
            for dependent in dependents:
                dependent_task = self.task_repo.get_task(dependent.task_id)
                if not dependent_task:
                    continue

                # Check if all dependencies satisfied
                unmet = self.dep_repo.find_unmet_dependencies(dependent.task_id)
                if not unmet:
                    # Transition regardless of current status (CREATED, BLOCKED, or ASSIGNED)
                    if dependent_task.status in [TaskStatus.CREATED, TaskStatus.BLOCKED]:
                        dependent_task.status = TaskStatus.ASSIGNED
                        dependent_task.version += 1

            self.audit_logger.log(
                user_id=user_id,
                action="TASK_COMPLETED",
                target_id=task_id,
                details={
                    "version": task.version,
                    "completion_notes": completion_notes,
                },
            )

            self.session.commit()
            return task

        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to complete task: {e}")
            raise

    def cancel_task(
        self,
        task_id: str,
        expected_version: int,
        reason: str = "",
        user_id: Optional[str] = None,
    ) -> InvestigationTask:
        """Cancel task (no longer needed).

        Transition: CREATED/ASSIGNED/ACTIVE -> CANCELLED

        Args:
            task_id: Task to cancel
            expected_version: Current version (concurrency check)
            reason: Reason for cancellation
            user_id: User cancelling (for audit)

        Returns:
            Updated task

        Raises:
            ValueError: If invalid status or version mismatch
        """
        try:
            task = self.task_repo.cancel_task(task_id, expected_version, reason)

            self.audit_logger.log(
                user_id=user_id,
                action="TASK_CANCELLED",
                target_id=task_id,
                details={"reason": reason, "version": task.version},
            )

            self.session.commit()
            return task

        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to cancel task: {e}")
            raise

    def skip_task(
        self,
        task_id: str,
        expected_version: int,
        reason: str = "",
        user_id: Optional[str] = None,
    ) -> InvestigationTask:
        """Skip task (not applicable to this investigation).

        Transition: ASSIGNED/ACTIVE -> SKIPPED

        Args:
            task_id: Task to skip
            expected_version: Current version (concurrency check)
            reason: Reason for skipping
            user_id: User skipping (for audit)

        Returns:
            Updated task

        Raises:
            ValueError: If invalid status or version mismatch
        """
        try:
            task = self.task_repo.skip_task(task_id, expected_version)

            self.audit_logger.log(
                user_id=user_id,
                action="TASK_SKIPPED",
                target_id=task_id,
                details={"reason": reason, "version": task.version},
            )

            self.session.commit()
            return task

        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to skip task: {e}")
            raise

    def block_task(
        self,
        task_id: str,
        expected_version: int,
        reason: str = "",
        user_id: Optional[str] = None,
    ) -> InvestigationTask:
        """Block task (waiting for external input).

        Transition: ACTIVE -> BLOCKED

        Args:
            task_id: Task to block
            expected_version: Current version (concurrency check)
            reason: What we're waiting for
            user_id: User blocking (for audit)

        Returns:
            Updated task

        Raises:
            ValueError: If invalid status or version mismatch
        """
        try:
            task = self.task_repo.block_task(task_id, expected_version, reason)

            self.audit_logger.log(
                user_id=user_id,
                action="TASK_BLOCKED",
                target_id=task_id,
                details={"reason": reason, "version": task.version},
            )

            self.session.commit()
            return task

        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to block task: {e}")
            raise

    def unblock_task(
        self,
        task_id: str,
        expected_version: int,
        user_id: Optional[str] = None,
    ) -> InvestigationTask:
        """Resume blocked task.

        Transition: BLOCKED -> ACTIVE

        Args:
            task_id: Task to resume
            expected_version: Current version (concurrency check)
            user_id: User resuming (for audit)

        Returns:
            Updated task

        Raises:
            ValueError: If invalid status or version mismatch
        """
        try:
            task = self.task_repo.unblock_task(task_id, expected_version)

            self.audit_logger.log(
                user_id=user_id,
                action="TASK_UNBLOCKED",
                target_id=task_id,
                details={"version": task.version},
            )

            self.session.commit()
            return task

        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to unblock task: {e}")
            raise

    def get_investigation_progress(
        self,
        investigation_id: str,
    ) -> Dict[str, Any]:
        """Get overall task progress for investigation.

        Returns:
            {
                "total_tasks": int,
                "status_breakdown": Dict[str, int],
                "completed": int,
                "percent_complete": float (0-100),
                "next_due_task": Optional[InvestigationTask],
                "blocked_tasks": List[InvestigationTask],
                "overdue_tasks": List[InvestigationTask],
            }
        """
        # Finding 10 fix: Use database-level aggregation instead of Python iteration
        from sqlalchemy import func

        # Get status breakdown via aggregation
        status_counts = dict(
            self.session.query(
                InvestigationTask.status,
                func.count().label('count')
            ).filter_by(investigation_id=investigation_id).group_by(
                InvestigationTask.status
            ).all()
        )

        # Extract counts for each status (before converting to strings)
        total_completed = status_counts.get(TaskStatus.COMPLETED, 0)
        total_skipped = status_counts.get(TaskStatus.SKIPPED, 0)
        total_cancelled = status_counts.get(TaskStatus.CANCELLED, 0)

        # Convert to string keys for response
        status_counts = {s.value if hasattr(s, 'value') else str(s): v for s, v in status_counts.items()}

        total_tasks = sum(status_counts.values())
        actionable_count = total_tasks - total_skipped - total_cancelled
        completed = total_completed
        percent = (completed / actionable_count * 100) if actionable_count > 0 else 0.0

        # Find next due task (earliest unfinished task with a due date)
        next_due = self.session.query(InvestigationTask).filter(
            InvestigationTask.investigation_id == investigation_id,
            InvestigationTask.due_at.isnot(None),
            InvestigationTask.status.notin_([TaskStatus.COMPLETED, TaskStatus.CANCELLED, TaskStatus.SKIPPED])
        ).order_by(InvestigationTask.due_at).first()

        # Find blocked tasks
        blocked = self.session.query(InvestigationTask).filter_by(
            investigation_id=investigation_id,
            status=TaskStatus.BLOCKED
        ).all()

        # Find overdue tasks
        overdue = self.task_repo.find_overdue_tasks(hours_before_due=0)
        overdue = [t for t in overdue if t.investigation_id == investigation_id]

        return {
            "total_tasks": total_tasks,
            "status_breakdown": status_counts,
            "completed": completed,
            "percent_complete": round(percent, 1),
            "next_due_task": next_due,
            "blocked_tasks": blocked,
            "overdue_tasks": overdue,
        }

    def get_task_dependency_graph(
        self,
        investigation_id: str,
    ) -> Dict[str, Any]:
        """Get dependency graph for investigation tasks.

        Returns:
            {
                "tasks": [task data],
                "dependencies": [dep data],
                "cycles_detected": bool,
            }
        """
        tasks = self.task_repo.list_tasks_by_investigation(
            investigation_id,
            include_completed=True,
        )

        task_ids = {t.id for t in tasks}
        dependencies = []

        for task in tasks:
            deps = self.dep_repo.list_dependencies(task.id)
            for dep in deps:
                if dep.depends_on_task_id in task_ids:
                    dependencies.append({
                        "from": task.id,
                        "to": dep.depends_on_task_id,
                        "type": dep.dependency_type.value,
                    })

        return {
            "tasks": [
                {
                    "id": t.id,
                    "title": t.title,
                    "status": t.status.value,
                    "priority": t.priority.value,
                    "category": t.category.value,
                }
                for t in tasks
            ],
            "dependencies": dependencies,
        }

    def update_all_sla_states(self) -> Dict[str, int]:
        """Scan all open tasks, update SLA states.

        Returns:
            {"normal": count, "warning": count, "breached": count}
        """
        return self.task_repo.update_sla_states()

    def batch_check_sla_breaches(self) -> List[Tuple[InvestigationTask, str]]:
        """Find all tasks that have breached SLA.

        Called periodically (e.g., every hour) to identify escalations.

        Returns:
            List of (task, investigation_id, breach_age_hours) tuples
        """
        overdue = self.task_repo.find_overdue_tasks(hours_before_due=0)

        breaches = []
        for task in overdue:
            if task.due_at and task.sla_state == SLAState.BREACHED:
                breach_age = (datetime.utcnow() - task.due_at).total_seconds() / 3600
                breaches.append((task, task.investigation_id, breach_age))

        return breaches

    def create_task_template(
        self,
        name: str,
        case_type: str,
        description: str = "",
        user_id: Optional[str] = None,
    ) -> TaskTemplate:
        """Create a new task template.

        Args:
            name: Template name (e.g., "Murder Investigation")
            case_type: Case type this template applies to
            description: Description of workflow
            user_id: User creating template (for audit)

        Returns:
            Created template
        """
        template = self.template_repo.create_template(name, case_type, description)

        self.audit_logger.log(
            user_id=user_id,
            action="TASK_TEMPLATE_CREATED",
            target_id=template.id,
            details={"case_type": case_type, "name": name},
        )

        self.session.commit()
        return template

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
        user_id: Optional[str] = None,
    ) -> TemplateTask:
        """Add a task to a template."""
        task = self.template_repo.add_template_task(
            template_id, order, title, description, category, priority,
            sla_hours, is_recurring, recurrence_interval_hours,
        )

        self.audit_logger.log(
            user_id=user_id,
            action="TEMPLATE_TASK_ADDED",
            target_id=template_id,
            details={"task_id": task.id, "order": order, "title": title},
        )

        self.session.commit()
        return task

    def add_template_dependency(
        self,
        template_id: str,
        task_id: str,
        depends_on_task_id: str,
        dependency_type: DependencyType = DependencyType.FINISH_TO_START,
        user_id: Optional[str] = None,
    ) -> None:
        """Add dependency between template tasks."""
        self.template_repo.add_template_dependency(
            template_id, task_id, depends_on_task_id, dependency_type
        )

        self.audit_logger.log(
            user_id=user_id,
            action="TEMPLATE_DEPENDENCY_ADDED",
            target_id=template_id,
            details={
                "task_id": task_id,
                "depends_on": depends_on_task_id,
                "type": dependency_type.value,
            },
        )

        self.session.commit()
