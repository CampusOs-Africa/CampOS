"""create milestone6 trust and fraud tables

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-30 19:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '0006'
down_revision: str | None = '0005'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. create trust_history table
    op.create_table(
        'trust_history',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('delta', sa.Integer(), nullable=False),
        sa.Column('old_score', sa.Integer(), nullable=False),
        sa.Column('new_score', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('reference_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_trust_history_user_id', 'trust_history', ['user_id'])
    op.create_index('ix_trust_history_event_type', 'trust_history', ['event_type'])
    op.create_index('ix_trust_history_reference_id', 'trust_history', ['reference_id'])
    op.create_index('ix_trust_history_created_at', 'trust_history', ['created_at'])

    # 2. create fraud_reports table
    op.create_table(
        'fraud_reports',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('reporter_id', sa.String(), nullable=False),
        sa.Column('reported_user_id', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('evidence_url', sa.String(), nullable=True),
        sa.Column('order_id', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('admin_id', sa.String(), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('penalty_applied', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['reporter_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reported_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['admin_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_fraud_reports_reporter_id', 'fraud_reports', ['reporter_id'])
    op.create_index('ix_fraud_reports_reported_user_id', 'fraud_reports', ['reported_user_id'])
    op.create_index('ix_fraud_reports_category', 'fraud_reports', ['category'])
    op.create_index('ix_fraud_reports_status', 'fraud_reports', ['status'])
    op.create_index('ix_fraud_reports_order_id', 'fraud_reports', ['order_id'])

    # 3. add review_type, status, moderated_by, moderation_reason columns to reviews table
    op.add_column('reviews', sa.Column('review_type', sa.String(), nullable=False, server_default='marketplace'))
    op.add_column('reviews', sa.Column('status', sa.String(), nullable=False, server_default='approved'))
    op.add_column('reviews', sa.Column('moderated_by', sa.String(), nullable=True))
    op.add_column('reviews', sa.Column('moderation_reason', sa.Text(), nullable=True))
    op.create_index('ix_reviews_review_type', 'reviews', ['review_type'])
    op.create_index('ix_reviews_status', 'reviews', ['status'])


def downgrade() -> None:
    op.drop_index('ix_reviews_status', table_name='reviews')
    op.drop_index('ix_reviews_review_type', table_name='reviews')
    op.drop_column('reviews', 'moderation_reason')
    op.drop_column('reviews', 'moderated_by')
    op.drop_column('reviews', 'status')
    op.drop_column('reviews', 'review_type')
    op.drop_table('fraud_reports')
    op.drop_table('trust_history')
