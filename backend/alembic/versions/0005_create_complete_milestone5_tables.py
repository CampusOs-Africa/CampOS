"""create complete milestone5 tables

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-30 16:00:00.000000

"""
from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa

from alembic import op

revision: str = '0005'
down_revision: str | None = '0004'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. create marketplace_categories table
    categories_table = op.create_table(
        'marketplace_categories',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('icon', sa.String(), nullable=True),
        sa.Column('active_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('ix_marketplace_categories_name', 'marketplace_categories', ['name'], unique=True)

    # Seed default categories
    now = datetime.now(UTC)
    op.bulk_insert(categories_table, [
        {"id": "books", "name": "Books & Notes", "description": "Textbooks, course notes & past questions", "icon": "BookOpen", "active_count": 0, "created_at": now},
        {"id": "electronics", "name": "Electronics", "description": "Laptops, phones & gadgets", "icon": "Laptop", "active_count": 0, "created_at": now},
        {"id": "accommodation", "name": "Housing", "description": "Hostels, apartments & room shares", "icon": "Home", "active_count": 0, "created_at": now},
        {"id": "tutoring", "name": "Tutoring", "description": "Academic coaching & group lessons", "icon": "GraduationCap", "active_count": 0, "created_at": now},
        {"id": "tickets", "name": "Event Tickets", "description": "Campus shows, seminars & NFT passes", "icon": "Ticket", "active_count": 0, "created_at": now},
        {"id": "services", "name": "Services", "description": "Laundry, repairs, fashion & design", "icon": "Wrench", "active_count": 0, "created_at": now},
    ])

    # 2. create order_items table
    op.create_table(
        'order_items',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('order_id', sa.String(), nullable=False),
        sa.Column('listing_id', sa.String(), nullable=False),
        sa.Column('seller_id', sa.String(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('price_per_unit', sa.Float(), nullable=False),
        sa.Column('subtotal', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['listing_id'], ['marketplace_listings.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['seller_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_order_items_order_id', 'order_items', ['order_id'])
    op.create_index('ix_order_items_listing_id', 'order_items', ['listing_id'])
    op.create_index('ix_order_items_seller_id', 'order_items', ['seller_id'])

    # 3. create escrow_records table
    op.create_table(
        'escrow_records',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('order_id', sa.String(), nullable=False),
        sa.Column('buyer_id', sa.String(), nullable=False),
        sa.Column('seller_id', sa.String(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('state', sa.String(), nullable=False, server_default='CREATED'),
        sa.Column('quai_order_id', sa.String(), nullable=False),
        sa.Column('escrow_tx_hash', sa.String(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['buyer_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['seller_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_id')
    )
    op.create_index('ix_escrow_records_order_id', 'escrow_records', ['order_id'], unique=True)
    op.create_index('ix_escrow_records_buyer_id', 'escrow_records', ['buyer_id'])
    op.create_index('ix_escrow_records_seller_id', 'escrow_records', ['seller_id'])
    op.create_index('ix_escrow_records_state', 'escrow_records', ['state'])
    op.create_index('ix_escrow_records_quai_order_id', 'escrow_records', ['quai_order_id'])
    op.create_index('ix_escrow_records_escrow_tx_hash', 'escrow_records', ['escrow_tx_hash'])

    # 4. add provider column to blip_payment_records
    op.add_column('blip_payment_records', sa.Column('provider', sa.String(), nullable=False, server_default='blip_pay'))


def downgrade() -> None:
    op.drop_column('blip_payment_records', 'provider')
    op.drop_table('escrow_records')
    op.drop_table('order_items')
    op.drop_table('marketplace_categories')
