"""initial verification tables

Revision ID: 0001
Revises: 
Create Date: 2026-07-30 12:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '0001'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    # create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('wallet_address', sa.String(), nullable=True),
        sa.Column('student_id', sa.String(), nullable=True),
        sa.Column('school', sa.String(), nullable=True),
        sa.Column('faculty', sa.String(), nullable=True),
        sa.Column('department', sa.String(), nullable=True),
        sa.Column('level', sa.String(), nullable=True),
        sa.Column('trust_score', sa.Integer(), nullable=False, server_default='50'),
        sa.Column('verification_status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('role', sa.String(), nullable=False, server_default='student'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_wallet_address', 'users', ['wallet_address'], unique=True)

    # create student_verifications table
    op.create_table(
        'student_verifications',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('student_id_url', sa.String(), nullable=False),
        sa.Column('admission_letter_url', sa.String(), nullable=False),
        sa.Column('university_email', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('approved_by', sa.String(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('credential_hash', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_student_verifications_user_id', 'student_verifications', ['user_id'])
    op.create_index('ix_student_verifications_status', 'student_verifications', ['status'])
    op.create_index('ix_student_verifications_university_email', 'student_verifications', ['university_email'])
    op.create_index('ix_student_verifications_credential_hash', 'student_verifications', ['credential_hash'])

    # create verification_history table
    op.create_table(
        'verification_history',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('verification_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('old_status', sa.String(), nullable=True),
        sa.Column('new_status', sa.String(), nullable=False),
        sa.Column('changed_by', sa.String(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['verification_id'], ['student_verifications.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['changed_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_verification_history_verification_id', 'verification_history', ['verification_id'])
    op.create_index('ix_verification_history_user_id', 'verification_history', ['user_id'])

def downgrade() -> None:
    op.drop_table('verification_history')
    op.drop_table('student_verifications')
    op.drop_table('users')
