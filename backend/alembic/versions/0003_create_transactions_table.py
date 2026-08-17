"""create transactions table

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-30 14:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '0003'
down_revision: str | None = '0002'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    op.create_table(
        'transactions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('wallet_address', sa.String(), nullable=False),
        sa.Column('recipient_address', sa.String(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('tx_hash', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False, server_default='send'),
        sa.Column('status', sa.String(), nullable=False, server_default='confirmed'),
        sa.Column('network', sa.String(), nullable=False, server_default='Quai Network Testnet'),
        sa.Column('block_number', sa.Integer(), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tx_hash')
    )
    op.create_index('ix_transactions_user_id', 'transactions', ['user_id'])
    op.create_index('ix_transactions_wallet_address', 'transactions', ['wallet_address'])
    op.create_index('ix_transactions_recipient_address', 'transactions', ['recipient_address'])
    op.create_index('ix_transactions_tx_hash', 'transactions', ['tx_hash'], unique=True)
    op.create_index('ix_transactions_type', 'transactions', ['type'])
    op.create_index('ix_transactions_status', 'transactions', ['status'])

def downgrade() -> None:
    op.drop_table('transactions')
