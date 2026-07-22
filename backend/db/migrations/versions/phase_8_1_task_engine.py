"""Phase 8.1: Task Engine Schema

Revision ID: 008_phase_8_1_tasks
Revises: 007_phase_7_3_intelligence
Create Date: 2026-07-21 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008_phase_8_1_tasks'
down_revision = '007_phase_7_3_intelligence'
branch_labels = None
depends_on = None


def upgrade():
    # Create enums
    taskstatus_enum = postgresql.ENUM('CREATED', 'ASSIGNED', 'ACTIVE', 'BLOCKED', 'COMPLETED', 'CANCELLED', 'SKIPPED', name='taskstatus')
    taskcategory_enum = postgresql.ENUM('EVIDENCE_COLLECTION', 'INTERVIEW', 'WARRANT', 'EXTERNAL_COORDINATION', 'ANALYSIS', 'FIELD_OPERATION', 'ADMINISTRATIVE', name='taskcategory')
    taskpriority_enum = postgresql.ENUM('CRITICAL', 'HIGH', 'MEDIUM', 'LOW', name='taskpriority')
    slastate_enum = postgresql.ENUM('NORMAL', 'WARNING', 'BREACHED', name='slastate')
    dependencytype_enum = postgresql.ENUM('FINISH_TO_START', 'START_TO_START', name='dependencytype')

    taskstatus_enum.create(op.get_bind())
    taskcategory_enum.create(op.get_bind())
    taskpriority_enum.create(op.get_bind())
    slastate_enum.create(op.get_bind())
    dependencytype_enum.create(op.get_bind())

    # Create task_templates table
    op.create_table(
        'task_templates',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('case_type', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_task_templates_case_type', 'task_templates', ['case_type'])
    op.create_index('ix_task_templates_active', 'task_templates', ['active'])
    op.create_index('ix_task_templates_name', 'task_templates', ['name'])

    # Create template_tasks table
    op.create_table(
        'template_tasks',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('template_id', sa.String(), nullable=True),
        sa.Column('order', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', taskcategory_enum, nullable=True),
        sa.Column('priority', taskpriority_enum, nullable=True),
        sa.Column('sla_hours', sa.Integer(), nullable=True),
        sa.Column('is_recurring', sa.Boolean(), nullable=True),
        sa.Column('recurrence_interval_hours', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['template_id'], ['task_templates.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_template_tasks_template_id', 'template_tasks', ['template_id'])

    # Create template_task_dependencies table
    op.create_table(
        'template_task_dependencies',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('task_id', sa.String(), nullable=True),
        sa.Column('depends_on_task_id', sa.String(), nullable=True),
        sa.Column('dependency_type', dependencytype_enum, nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['depends_on_task_id'], ['template_tasks.id'], ),
        sa.ForeignKeyConstraint(['task_id'], ['template_tasks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_template_task_dependencies_task_id', 'template_task_dependencies', ['task_id'])

    # Create investigation_tasks table (Finding 8 fix: Add SLA pause support)
    op.create_table(
        'investigation_tasks',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('investigation_id', sa.String(), nullable=True),
        sa.Column('template_task_id', sa.String(), nullable=True),
        sa.Column('parent_task_id', sa.String(), nullable=True),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', taskcategory_enum, nullable=True),
        sa.Column('priority', taskpriority_enum, nullable=True),
        sa.Column('status', taskstatus_enum, nullable=True),
        sa.Column('assigned_officer_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('assigned_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('due_at', sa.DateTime(), nullable=True),
        sa.Column('sla_hours', sa.Integer(), nullable=True),
        sa.Column('sla_state', slastate_enum, nullable=True),
        sa.Column('sla_escalated', sa.Boolean(), nullable=True),
        sa.Column('blocked_at', sa.DateTime(), nullable=True),
        sa.Column('total_blocked_seconds', sa.Integer(), nullable=True),
        sa.Column('is_recurring', sa.Boolean(), nullable=True),
        sa.Column('recurrence_interval_hours', sa.Integer(), nullable=True),
        sa.Column('next_recurrence_at', sa.DateTime(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['investigation_id'], ['investigations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_task_id'], ['investigation_tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_investigation_tasks_investigation_id', 'investigation_tasks', ['investigation_id'])
    op.create_index('ix_investigation_tasks_status', 'investigation_tasks', ['investigation_id', 'status'])
    op.create_index('ix_investigation_tasks_officer', 'investigation_tasks', ['assigned_officer_id', 'status'])
    op.create_index('ix_investigation_tasks_due', 'investigation_tasks', ['investigation_id', 'due_at'])
    op.create_index('ix_investigation_tasks_parent', 'investigation_tasks', ['parent_task_id'])

    # Create task_dependencies table
    op.create_table(
        'task_dependencies',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('task_id', sa.String(), nullable=True),
        sa.Column('depends_on_task_id', sa.String(), nullable=True),
        sa.Column('dependency_type', dependencytype_enum, nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['depends_on_task_id'], ['investigation_tasks.id'], ),
        sa.ForeignKeyConstraint(['task_id'], ['investigation_tasks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_task_dependencies_task_id', 'task_dependencies', ['task_id'])
    op.create_index('ix_task_dependencies_depends_on', 'task_dependencies', ['depends_on_task_id'])
    op.create_index('ix_task_dependencies_task_depends', 'task_dependencies', ['task_id', 'depends_on_task_id'])


def downgrade():
    # Drop tables in reverse order
    op.drop_index('ix_task_dependencies_task_depends', table_name='task_dependencies')
    op.drop_index('ix_task_dependencies_depends_on', table_name='task_dependencies')
    op.drop_index('ix_task_dependencies_task_id', table_name='task_dependencies')
    op.drop_table('task_dependencies')

    op.drop_index('ix_investigation_tasks_parent', table_name='investigation_tasks')
    op.drop_index('ix_investigation_tasks_due', table_name='investigation_tasks')
    op.drop_index('ix_investigation_tasks_officer', table_name='investigation_tasks')
    op.drop_index('ix_investigation_tasks_status', table_name='investigation_tasks')
    op.drop_index('ix_investigation_tasks_investigation_id', table_name='investigation_tasks')
    op.drop_table('investigation_tasks')

    op.drop_index('ix_template_task_dependencies_task_id', table_name='template_task_dependencies')
    op.drop_table('template_task_dependencies')

    op.drop_index('ix_template_tasks_template_id', table_name='template_tasks')
    op.drop_table('template_tasks')

    op.drop_index('ix_task_templates_name', table_name='task_templates')
    op.drop_index('ix_task_templates_active', table_name='task_templates')
    op.drop_index('ix_task_templates_case_type', table_name='task_templates')
    op.drop_table('task_templates')

    # Drop enums
    sa.Enum(name='dependencytype').drop(op.get_bind())
    sa.Enum(name='slastate').drop(op.get_bind())
    sa.Enum(name='taskpriority').drop(op.get_bind())
    sa.Enum(name='taskcategory').drop(op.get_bind())
    sa.Enum(name='taskstatus').drop(op.get_bind())
