"""Initial schema: users, devices, notification_events, open_loops, reminders

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-08-19 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users table
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('timezone', sa.String(length=50), nullable=False, server_default='UTC'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. devices table
    op.create_table(
        'devices',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('platform', sa.String(length=20), nullable=False),
        sa.Column('device_name', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_devices_user_id'), 'devices', ['user_id'], unique=False)

    # 3. notification_events table
    op.create_table(
        'notification_events',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('device_id', sa.UUID(), nullable=True),
        sa.Column('client_event_id', sa.String(length=255), nullable=True),
        sa.Column('source_app', sa.String(length=100), nullable=False),
        sa.Column('source_package', sa.String(length=255), nullable=False),
        sa.Column('sender', sa.String(length=255), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('processing_status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('processing_error', sa.Text(), nullable=True),
        sa.Column('ai_result', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=True),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'device_id', 'client_event_id', name='uq_user_device_client_event')
    )
    op.create_index(op.f('ix_notification_events_user_id'), 'notification_events', ['user_id'], unique=False)
    op.create_index(op.f('ix_notification_events_device_id'), 'notification_events', ['device_id'], unique=False)
    op.create_index(op.f('ix_notification_events_processing_status'), 'notification_events', ['processing_status'], unique=False)
    op.create_index('ix_notification_events_status_received', 'notification_events', ['processing_status', 'received_at'], unique=False)

    # 4. open_loops table
    op.create_table(
        'open_loops',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('source_notification_id', sa.UUID(), nullable=True),
        sa.Column('task', sa.Text(), nullable=False),
        sa.Column('person', sa.String(length=255), nullable=True),
        sa.Column('deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deadline_text', sa.String(length=255), nullable=True),
        sa.Column('importance', sa.String(length=20), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='open'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['source_notification_id'], ['notification_events.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_open_loops_user_id'), 'open_loops', ['user_id'], unique=False)
    op.create_index(op.f('ix_open_loops_source_notification_id'), 'open_loops', ['source_notification_id'], unique=False)
    op.create_index(op.f('ix_open_loops_status'), 'open_loops', ['status'], unique=False)
    op.create_index('ix_open_loops_user_status', 'open_loops', ['user_id', 'status'], unique=False)

    # 5. reminders table
    op.create_table(
        'reminders',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('open_loop_id', sa.UUID(), nullable=False),
        sa.Column('scheduled_for', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='scheduled'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('triggered_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['open_loop_id'], ['open_loops.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reminders_user_id'), 'reminders', ['user_id'], unique=False)
    op.create_index(op.f('ix_reminders_open_loop_id'), 'reminders', ['open_loop_id'], unique=False)
    op.create_index(op.f('ix_reminders_status'), 'reminders', ['status'], unique=False)
    op.create_index('ix_reminders_user_status_scheduled', 'reminders', ['user_id', 'status', 'scheduled_for'], unique=False)


def downgrade() -> None:
    op.drop_table('reminders')
    op.drop_table('open_loops')
    op.drop_table('notification_events')
    op.drop_table('devices')
    op.drop_table('users')
