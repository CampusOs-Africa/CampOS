"""add tx_hash to student_verifications

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-30 13:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '0002'
down_revision: str | None = '0001'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    op.add_column('student_verifications', sa.Column('tx_hash', sa.String(), nullable=True))
    op.create_index(
        'ix_student_verifications_tx_hash',
        'student_verifications',
        ['tx_hash'],
        unique=False
    )

def downgrade() -> None:
    op.drop_index('ix_student_verifications_tx_hash', table_name='student_verifications')
    op.drop_column('student_verifications', 'tx_hash')
