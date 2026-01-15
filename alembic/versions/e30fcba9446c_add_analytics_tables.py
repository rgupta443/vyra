"""add_analytics_tables

Revision ID: e30fcba9446c
Revises: 93fdf14be379
Create Date: 2026-01-16 02:27:42.316479

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e30fcba9446c'
down_revision = '93fdf14be379'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create analytics_events table
    op.create_table(
        'analytics_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('event_data', postgresql.JSON(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_analytics_events_event_type', 'analytics_events', ['event_type'])
    op.create_index('ix_analytics_events_created_at', 'analytics_events', ['created_at'])
    
    # Create system_metrics table
    op.create_table(
        'system_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('metric_name', sa.String(), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('metric_unit', sa.String(), nullable=True),
        sa.Column('tags', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_system_metrics_metric_name', 'system_metrics', ['metric_name'])
    op.create_index('ix_system_metrics_created_at', 'system_metrics', ['created_at'])
    
    # Create conversion_metrics table
    op.create_table(
        'conversion_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('from_plan', sa.String(), nullable=False),
        sa.Column('to_plan', sa.String(), nullable=False),
        sa.Column('generations_before_conversion', sa.Integer(), nullable=True),
        sa.Column('days_since_signup', sa.Integer(), nullable=True),
        sa.Column('converted_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_conversion_metrics_converted_at', 'conversion_metrics', ['converted_at'])


def downgrade() -> None:
    op.drop_index('ix_conversion_metrics_converted_at', 'conversion_metrics')
    op.drop_table('conversion_metrics')
    
    op.drop_index('ix_system_metrics_created_at', 'system_metrics')
    op.drop_index('ix_system_metrics_metric_name', 'system_metrics')
    op.drop_table('system_metrics')
    
    op.drop_index('ix_analytics_events_created_at', 'analytics_events')
    op.drop_index('ix_analytics_events_event_type', 'analytics_events')
    op.drop_table('analytics_events')