"""Unit tests for Phase 8.1 Task Engine.

Tests task lifecycle, dependencies, templates, SLA tracking, and optimistic locking.
All tests use in-memory SQLite for isolation.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from uuid import uuid4

from backend.db.schema import Base, TaskStatus, TaskCategory, TaskPriority, DependencyType
from backend.repositories.task_repository import (
    TaskRepository, DependencyRepository, TaskTemplateRepository
)
from backend.services.task_engine import TaskEngine
from backend.audit.audit_logger import AuditLogger


@pytest.fixture
def db_session() -> Session:
    """In-memory SQLite session for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def investigation_id() -> str:
    """Sample investigation ID."""
    return f"INV-{uuid4()}"


@pytest.fixture
def officer_id() -> str:
    """Sample officer ID."""
    return f"OFF-{uuid4()}"


@pytest.fixture
def user_id() -> str:
    """Sample user ID."""
    return f"USR-{uuid4()}"


@pytest.fixture
def task_repo(db_session: Session) -> TaskRepository:
    """Task repository."""
    return TaskRepository(db_session)


@pytest.fixture
def dep_repo(db_session: Session) -> DependencyRepository:
    """Dependency repository."""
    return DependencyRepository(db_session)


@pytest.fixture
def template_repo(db_session: Session) -> TaskTemplateRepository:
    """Template repository."""
    return TaskTemplateRepository(db_session)


@pytest.fixture
def engine(db_session: Session) -> TaskEngine:
    """Task engine with audit logger."""
    audit_logger = AuditLogger(db_session)
    return TaskEngine(db_session, audit_logger)


class TestTaskLifecycle:
    """Test task status transitions."""

    def test_create_task(self, task_repo: TaskRepository, investigation_id: str):
        """Create task in CREATED state."""
        task = task_repo.create_task(
            investigation_id=investigation_id,
            title="Collect Evidence",
            description="Collect physical evidence from scene",
            category=TaskCategory.EVIDENCE_COLLECTION,
            priority=TaskPriority.HIGH,
            sla_hours=72,
        )

        assert task.id is not None
        assert task.investigation_id == investigation_id
        assert task.status == TaskStatus.CREATED
        assert task.version == 1
        assert task.due_at is not None

    def test_assign_task(self, task_repo: TaskRepository, investigation_id: str, officer_id: str):
        """Assign task: CREATED -> ASSIGNED."""
        task = task_repo.create_task(
            investigation_id=investigation_id,
            title="Collect Evidence",
            description="",
            category=TaskCategory.EVIDENCE_COLLECTION,
            priority=TaskPriority.HIGH,
        )

        assigned = task_repo.assign_task(task.id, officer_id, task.version)

        assert assigned.status == TaskStatus.ASSIGNED
        assert assigned.assigned_officer_id == officer_id
        assert assigned.assigned_at is not None
        assert assigned.version == 2

    def test_start_task(self, engine: TaskEngine, investigation_id: str, officer_id: str):
        """Start task: ASSIGNED -> ACTIVE."""
        task = engine.task_repo.create_task(
            investigation_id=investigation_id,
            title="Collect Evidence",
            description="",
            category=TaskCategory.EVIDENCE_COLLECTION,
            priority=TaskPriority.HIGH,
        )
        task = engine.task_repo.assign_task(task.id, officer_id, task.version)

        task = engine.start_task(task.id, task.version)

        assert task.status == TaskStatus.ACTIVE
        assert task.started_at is not None

    def test_complete_task(self, engine: TaskEngine, investigation_id: str, officer_id: str):
        """Complete task: ACTIVE -> COMPLETED."""
        task = engine.task_repo.create_task(
            investigation_id=investigation_id,
            title="Collect Evidence",
            description="",
            category=TaskCategory.EVIDENCE_COLLECTION,
            priority=TaskPriority.HIGH,
        )
        task = engine.task_repo.assign_task(task.id, officer_id, task.version)
        task = engine.task_repo.session.query(type(task)).filter_by(id=task.id).first()
        task.status = TaskStatus.ACTIVE
        task.version += 1
        engine.task_repo.session.flush()

        task = engine.complete_task(task.id, task.version)

        assert task.status == TaskStatus.COMPLETED
        assert task.completed_at is not None

    def test_cancel_task(self, engine: TaskEngine, investigation_id: str):
        """Cancel task: CREATED -> CANCELLED."""
        task = engine.task_repo.create_task(
            investigation_id=investigation_id,
            title="Collect Evidence",
            description="",
            category=TaskCategory.EVIDENCE_COLLECTION,
            priority=TaskPriority.HIGH,
        )

        task = engine.cancel_task(task.id, task.version, reason="Evidence not available")

        assert task.status == TaskStatus.CANCELLED

    def test_skip_task(self, engine: TaskEngine, investigation_id: str, officer_id: str):
        """Skip task: ASSIGNED -> SKIPPED."""
        task = engine.task_repo.create_task(
            investigation_id=investigation_id,
            title="Collect Evidence",
            description="",
            category=TaskCategory.EVIDENCE_COLLECTION,
            priority=TaskPriority.HIGH,
        )
        task = engine.task_repo.assign_task(task.id, officer_id, task.version)

        task = engine.skip_task(task.id, task.version, reason="Not applicable")

        assert task.status == TaskStatus.SKIPPED

    def test_block_task(self, task_repo: TaskRepository, investigation_id: str):
        """Block task: ACTIVE -> BLOCKED."""
        task = task_repo.create_task(
            investigation_id=investigation_id,
            title="Collect Evidence",
            description="",
            category=TaskCategory.EVIDENCE_COLLECTION,
            priority=TaskPriority.HIGH,
        )
        task = task_repo.session.query(type(task)).filter_by(id=task.id).first()
        task.status = TaskStatus.ACTIVE
        task.version += 1
        task_repo.session.flush()

        blocked = task_repo.block_task(task.id, task.version, reason="Waiting for lab")

        assert blocked.status == TaskStatus.BLOCKED


class TestDependencies:
    """Test task dependencies and blocking."""

    def test_create_dependency(self, dep_repo: DependencyRepository, task_repo: TaskRepository, investigation_id: str):
        """Create finish-to-start dependency."""
        task1 = task_repo.create_task(
            investigation_id=investigation_id,
            title="Task 1",
            description="",
            category=TaskCategory.EVIDENCE_COLLECTION,
            priority=TaskPriority.HIGH,
        )
        task2 = task_repo.create_task(
            investigation_id=investigation_id,
            title="Task 2",
            description="",
            category=TaskCategory.ANALYSIS,
            priority=TaskPriority.MEDIUM,
        )

        dep = dep_repo.create_dependency(
            task2.id,
            task1.id,
            DependencyType.FINISH_TO_START,
        )

        assert dep.task_id == task2.id
        assert dep.depends_on_task_id == task1.id

    def test_cannot_start_task_with_unmet_dependency(
        self,
        engine: TaskEngine,
        investigation_id: str,
        officer_id: str,
    ):
        """Cannot start task if dependency not completed."""
        task1 = engine.task_repo.create_task(
            investigation_id=investigation_id,
            title="Task 1",
            description="",
            category=TaskCategory.EVIDENCE_COLLECTION,
            priority=TaskPriority.HIGH,
        )
        task2 = engine.task_repo.create_task(
            investigation_id=investigation_id,
            title="Task 2",
            description="",
            category=TaskCategory.ANALYSIS,
            priority=TaskPriority.MEDIUM,
        )

        # Create dependency: task2 depends on task1
        engine.dep_repo.create_dependency(
            task2.id,
            task1.id,
            DependencyType.FINISH_TO_START,
        )

        # Assign task2 but don't complete task1
        task2 = engine.task_repo.assign_task(task2.id, officer_id, task2.version)

        # Should not be able to start task2
        with pytest.raises(ValueError, match="Unmet dependencies"):
            engine.start_task(task2.id, task2.version)

    def test_task_can_start_after_dependency_complete(
        self,
        engine: TaskEngine,
        investigation_id: str,
        officer_id: str,
    ):
        """Task can start after dependency is completed."""
        task1 = engine.task_repo.create_task(
            investigation_id=investigation_id,
            title="Task 1",
            description="",
            category=TaskCategory.EVIDENCE_COLLECTION,
            priority=TaskPriority.HIGH,
        )
        task2 = engine.task_repo.create_task(
            investigation_id=investigation_id,
            title="Task 2",
            description="",
            category=TaskCategory.ANALYSIS,
            priority=TaskPriority.MEDIUM,
        )

        # Create dependency
        engine.dep_repo.create_dependency(
            task2.id,
            task1.id,
            DependencyType.FINISH_TO_START,
        )

        # Complete task1
        task1 = engine.task_repo.assign_task(task1.id, officer_id, task1.version)
        task1 = engine.task_repo.session.query(type(task1)).filter_by(id=task1.id).first()
        task1.status = TaskStatus.ACTIVE
        task1.version += 1
        engine.task_repo.session.flush()

        task1 = engine.complete_task(task1.id, task1.version)
        assert task1.status == TaskStatus.COMPLETED

        # task2 should auto-transition to ASSIGNED after task1 completes
        task2 = engine.task_repo.get_task(task2.id)
        assert task2.status == TaskStatus.ASSIGNED

        # Now task2 should be able to start
        task2 = engine.start_task(task2.id, task2.version)
        assert task2.status == TaskStatus.ACTIVE

    def test_circular_dependency_prevented(
        self,
        dep_repo: DependencyRepository,
        task_repo: TaskRepository,
        investigation_id: str,
    ):
        """Circular dependencies rejected."""
        task1 = task_repo.create_task(
            investigation_id=investigation_id,
            title="Task 1",
            description="",
            category=TaskCategory.EVIDENCE_COLLECTION,
            priority=TaskPriority.HIGH,
        )
        task2 = task_repo.create_task(
            investigation_id=investigation_id,
            title="Task 2",
            description="",
            category=TaskCategory.ANALYSIS,
            priority=TaskPriority.MEDIUM,
        )

        # Create task1 -> task2
        dep_repo.create_dependency(task1.id, task2.id)

        # Try to create task2 -> task1 (would create cycle)
        with pytest.raises(ValueError, match="circular"):
            dep_repo.create_dependency(task2.id, task1.id)


class TestRecurringTasks:
    """Test recurring task automation."""

    def test_recurring_task_creation(self, engine: TaskEngine, investigation_id: str):
        """Completing recurring task creates next instance."""
        task = engine.task_repo.create_task(
            investigation_id=investigation_id,
            title="Daily Status Check",
            description="",
            category=TaskCategory.ADMINISTRATIVE,
            priority=TaskPriority.MEDIUM,
            sla_hours=24,
            is_recurring=True,
            recurrence_interval_hours=24,
        )

        # Set to ACTIVE to complete
        task = engine.task_repo.session.query(type(task)).filter_by(id=task.id).first()
        task.status = TaskStatus.ACTIVE
        task.version += 1
        engine.task_repo.session.flush()

        # Complete task
        engine.task_repo.complete_task(task.id, task.version)

        # Check that next task was created
        next_tasks = engine.task_repo.list_tasks_by_investigation(
            investigation_id,
            include_completed=True,
        )
        assert len(next_tasks) == 2  # Original + new
        assert next_tasks[-1].status == TaskStatus.CREATED


class TestSLATracking:
    """Test SLA state management."""

    def test_sla_calculation_normal(self, task_repo: TaskRepository, investigation_id: str):
        """Task with due date far in future is NORMAL."""
        task = task_repo.create_task(
            investigation_id=investigation_id,
            title="Task",
            description="",
            category=TaskCategory.EVIDENCE_COLLECTION,
            priority=TaskPriority.HIGH,
            sla_hours=72,
        )

        assert task.sla_state == "NORMAL"
        assert task.due_at > datetime.utcnow() + timedelta(hours=24)

    def test_sla_warning_state(self, task_repo: TaskRepository, investigation_id: str):
        """Task approaching SLA is WARNING."""
        task = task_repo.create_task(
            investigation_id=investigation_id,
            title="Task",
            description="",
            category=TaskCategory.EVIDENCE_COLLECTION,
            priority=TaskPriority.HIGH,
            sla_hours=2,  # 2 hours
        )

        import time
        time.sleep(0.1)  # Let some time pass

        counts = task_repo.update_sla_states()

        # After time passes, should be WARNING or BREACHED
        task = task_repo.get_task(task.id)
        assert task.sla_state in ["WARNING", "BREACHED"]

    def test_sla_breach_detection(self, task_repo: TaskRepository, investigation_id: str):
        """Overdue task is BREACHED."""
        task = task_repo.create_task(
            investigation_id=investigation_id,
            title="Task",
            description="",
            category=TaskCategory.EVIDENCE_COLLECTION,
            priority=TaskPriority.HIGH,
            sla_hours=-1,  # Already due
        )

        counts = task_repo.update_sla_states()

        task = task_repo.get_task(task.id)
        assert task.sla_state == "BREACHED"
        assert counts["breached"] >= 1


class TestOptimisticLocking:
    """Test concurrent modification detection."""

    def test_concurrent_modification_rejected(
        self,
        task_repo: TaskRepository,
        investigation_id: str,
        officer_id: str,
    ):
        """Version mismatch prevents concurrent updates."""
        task = task_repo.create_task(
            investigation_id=investigation_id,
            title="Task",
            description="",
            category=TaskCategory.EVIDENCE_COLLECTION,
            priority=TaskPriority.HIGH,
        )

        # Save the version before concurrent update
        stale_version = task.version

        # Simulate concurrent update (this modifies task in-place)
        task_repo.assign_task(task.id, officer_id, stale_version)

        # Try to update with stale version
        with pytest.raises(ValueError, match="Concurrent modification"):
            task_repo.update_task(
                task.id,
                stale_version,  # Use saved stale version
                title="Updated"
            )

    def test_concurrent_start_task_conflict(
        self,
        engine: TaskEngine,
        investigation_id: str,
        officer_id: str,
    ):
        """Concurrent starts on same task should conflict (Finding 12 fix)."""
        task = engine.task_repo.create_task(
            investigation_id=investigation_id,
            title="Task",
            description="",
            category=TaskCategory.EVIDENCE_COLLECTION,
            priority=TaskPriority.HIGH,
        )

        # Assign task
        task = engine.task_repo.assign_task(task.id, officer_id, task.version)
        original_version = task.version

        # Simulate concurrent start: first thread succeeds
        task1_after_start = engine.start_task(task.id, original_version)
        assert task1_after_start.status == TaskStatus.ACTIVE
        assert task1_after_start.version == original_version + 1

        # Second thread tries to start with stale version
        # Fails because task is already ACTIVE (status check happens before version check)
        with pytest.raises(ValueError, match="Cannot start task in|Concurrent modification"):
            engine.start_task(task.id, original_version)  # Stale version


class TestTemplates:
    """Test task template functionality."""

    def test_create_template(self, template_repo: TaskTemplateRepository):
        """Create task template."""
        template = template_repo.create_template(
            name="Murder Investigation",
            case_type="MURDER",
            description="Standard murder investigation workflow",
        )

        assert template.id is not None
        assert template.case_type == "MURDER"
        assert template.active is True

    def test_add_template_tasks(self, template_repo: TaskTemplateRepository):
        """Add tasks to template."""
        template = template_repo.create_template(
            name="Murder Investigation",
            case_type="MURDER",
        )

        task1 = template_repo.add_template_task(
            template.id,
            order=1,
            title="Secure Crime Scene",
            description="",
            category=TaskCategory.ADMINISTRATIVE,
            priority=TaskPriority.CRITICAL,
            sla_hours=2,
        )

        task2 = template_repo.add_template_task(
            template.id,
            order=2,
            title="Collect Physical Evidence",
            description="",
            category=TaskCategory.EVIDENCE_COLLECTION,
            priority=TaskPriority.HIGH,
            sla_hours=72,
        )

        # Add dependency
        template_repo.add_template_dependency(
            template.id,
            task2.id,
            task1.id,
            DependencyType.FINISH_TO_START,
        )

        assert task1.order == 1
        assert task2.order == 2

    def test_instantiate_template(self, engine: TaskEngine, investigation_id: str):
        """Instantiate template creates tasks with dependencies."""
        # Create template
        template = engine.template_repo.create_template(
            name="Murder Investigation",
            case_type="MURDER",
        )

        task1 = engine.template_repo.add_template_task(
            template.id,
            order=1,
            title="Secure Crime Scene",
            description="",
            category=TaskCategory.ADMINISTRATIVE,
            priority=TaskPriority.CRITICAL,
        )

        task2 = engine.template_repo.add_template_task(
            template.id,
            order=2,
            title="Collect Evidence",
            description="",
            category=TaskCategory.EVIDENCE_COLLECTION,
            priority=TaskPriority.HIGH,
        )

        engine.template_repo.add_template_dependency(
            template.id,
            task2.id,
            task1.id,
        )

        # Instantiate
        tasks = engine.template_repo.instantiate_template(template.id, investigation_id)

        assert len(tasks) == 2
        assert tasks[0].title == "Secure Crime Scene"
        assert tasks[1].title == "Collect Evidence"


class TestProgressTracking:
    """Test investigation progress calculation."""

    def test_progress_calculation(self, engine: TaskEngine, investigation_id: str, officer_id: str):
        """Calculate progress correctly."""
        # Create 4 tasks
        for i in range(4):
            engine.task_repo.create_task(
                investigation_id=investigation_id,
                title=f"Task {i}",
                description="",
                category=TaskCategory.EVIDENCE_COLLECTION,
                priority=TaskPriority.HIGH,
            )

        tasks = engine.task_repo.list_tasks_by_investigation(investigation_id, include_completed=True)
        assert len(tasks) == 4

        # Complete 1
        task = tasks[0]
        task = engine.task_repo.assign_task(task.id, officer_id, task.version)
        task = engine.task_repo.session.query(type(task)).filter_by(id=task.id).first()
        task.status = TaskStatus.ACTIVE
        task.version += 1
        engine.task_repo.session.flush()

        engine.task_repo.complete_task(task.id, task.version)

        # Get progress
        progress = engine.get_investigation_progress(investigation_id)

        assert progress["total_tasks"] == 4
        assert progress["completed"] == 1
        assert progress["percent_complete"] == 25.0

    def test_progress_excludes_skipped_and_cancelled(self, engine: TaskEngine, investigation_id: str, officer_id: str):
        """Progress calculation excludes skipped/cancelled tasks (Finding 15 fix)."""
        # Create 10 tasks
        for i in range(10):
            engine.task_repo.create_task(
                investigation_id=investigation_id,
                title=f"Task {i}",
                description="",
                category=TaskCategory.EVIDENCE_COLLECTION,
                priority=TaskPriority.HIGH,
            )

        tasks = engine.task_repo.list_tasks_by_investigation(investigation_id, include_completed=True)

        # Complete 3 tasks
        for i in range(3):
            task = tasks[i]
            task = engine.task_repo.assign_task(task.id, officer_id, task.version)
            task = engine.task_repo.session.query(type(task)).filter_by(id=task.id).first()
            task.status = TaskStatus.ACTIVE
            task.version += 1
            engine.task_repo.session.flush()
            engine.task_repo.complete_task(task.id, task.version)

        # Skip 2 tasks
        for i in range(3, 5):
            task = tasks[i]
            task = engine.task_repo.assign_task(task.id, officer_id, task.version)
            engine.task_repo.skip_task(task.id, task.version)

        # Cancel 2 tasks
        for i in range(5, 7):
            task = tasks[i]
            engine.task_repo.cancel_task(task.id, task.version)

        # Remaining 3 tasks are CREATED (not terminal yet)

        progress = engine.get_investigation_progress(investigation_id)

        # Only 6 actionable tasks (10 - 2 skipped - 2 cancelled, CREATED tasks are actionable)
        # 3 completed out of 6 = 50%
        assert progress["completed"] == 3
        assert abs(progress["percent_complete"] - 50.0) < 0.1


class TestPerformance:
    """Performance benchmarks (Finding 11 fix)."""

    def test_progress_calculation_performance_1k_tasks(self, engine: TaskEngine, investigation_id: str):
        """Progress calculation should be O(log N) with database aggregation."""
        import time

        # Create 1000 tasks
        for i in range(1000):
            engine.task_repo.create_task(
                investigation_id=investigation_id,
                title=f"Task {i}",
                description="",
                category=TaskCategory.EVIDENCE_COLLECTION,
                priority=TaskPriority.HIGH,
            )

        engine.task_repo.session.flush()

        # Measure progress calculation time
        start = time.time()
        progress = engine.get_investigation_progress(investigation_id)
        elapsed = time.time() - start

        assert progress["total_tasks"] == 1000
        assert elapsed < 0.1, f"Progress calculation took {elapsed}s, should be < 100ms"

    def test_task_creation_performance(self, task_repo: TaskRepository, investigation_id: str):
        """Task creation should be O(1)."""
        import time

        start = time.time()
        task = task_repo.create_task(
            investigation_id=investigation_id,
            title="Test Task",
            description="",
            category=TaskCategory.EVIDENCE_COLLECTION,
            priority=TaskPriority.HIGH,
        )
        elapsed = time.time() - start

        assert task.id is not None
        assert elapsed < 0.05, f"Task creation took {elapsed}s, should be < 50ms"

    def test_template_instantiation_performance(self, engine: TaskEngine, investigation_id: str):
        """Template instantiation with 13 tasks should be < 100ms."""
        import time

        template = engine.template_repo.create_template(
            name="Test Template",
            case_type="TEST",
            description="",
        )

        # Add 13 tasks like murder template
        for i in range(13):
            engine.template_repo.add_template_task(
                template.id,
                order=i,
                title=f"Task {i}",
                description="",
                category=TaskCategory.EVIDENCE_COLLECTION,
                priority=TaskPriority.HIGH,
                sla_hours=24,
            )

        engine.task_repo.session.flush()

        # Measure instantiation time
        start = time.time()
        tasks = engine.template_repo.instantiate_template(template.id, investigation_id)
        elapsed = time.time() - start

        assert len(tasks) == 13
        assert elapsed < 0.1, f"Instantiation took {elapsed}s, should be < 100ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
