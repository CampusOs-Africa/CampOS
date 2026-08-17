"""Add student-profile fields to users.

Revision ID: 0008
Revises: 0007
Create Date: 2026-08-16 10:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("phone", sa.String(), nullable=True))
    op.add_column("users", sa.Column("date_of_birth", sa.String(), nullable=True))
    op.add_column("users", sa.Column("gender", sa.String(), nullable=True))
    op.add_column("users", sa.Column("matric_number", sa.String(), nullable=True))
    op.add_column("users", sa.Column("admission_year", sa.String(), nullable=True))
    op.add_column("users", sa.Column("school_email", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "school_email")
    op.drop_column("users", "admission_year")
    op.drop_column("users", "matric_number")
    op.drop_column("users", "gender")
    op.drop_column("users", "date_of_birth")
    op.drop_column("users", "phone")
