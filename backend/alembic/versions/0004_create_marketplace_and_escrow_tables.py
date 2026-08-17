"""create marketplace and escrow tables

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-30 15:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '0004'
down_revision: str | None = '0003'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. create marketplace_listings table
    op.create_table(
        'marketplace_listings',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('seller_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('condition', sa.String(), nullable=False, server_default='good'),
        sa.Column('images', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='active'),
        sa.Column('inventory_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['seller_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_marketplace_listings_seller_id', 'marketplace_listings', ['seller_id'])
    op.create_index('ix_marketplace_listings_category', 'marketplace_listings', ['category'])
    op.create_index('ix_marketplace_listings_status', 'marketplace_listings', ['status'])
    op.create_index('ix_marketplace_category_status', 'marketplace_listings', ['category', 'status'])

    # 2. create orders table
    op.create_table(
        'orders',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('buyer_id', sa.String(), nullable=False),
        sa.Column('listing_id', sa.String(), nullable=False),
        sa.Column('seller_id', sa.String(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('payment_reference', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='initiated'),
        sa.Column('escrow_tx_hash', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['buyer_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['listing_id'], ['marketplace_listings.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['seller_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('payment_reference')
    )
    op.create_index('ix_orders_buyer_id', 'orders', ['buyer_id'])
    op.create_index('ix_orders_listing_id', 'orders', ['listing_id'])
    op.create_index('ix_orders_seller_id', 'orders', ['seller_id'])
    op.create_index('ix_orders_payment_reference', 'orders', ['payment_reference'], unique=True)
    op.create_index('ix_orders_status', 'orders', ['status'])
    op.create_index('ix_orders_escrow_tx_hash', 'orders', ['escrow_tx_hash'])
    op.create_index('ix_orders_buyer_status', 'orders', ['buyer_id', 'status'])
    op.create_index('ix_orders_seller_status', 'orders', ['seller_id', 'status'])

    # 3. create blip_payment_records table
    op.create_table(
        'blip_payment_records',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('order_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('payment_reference', sa.String(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(), nullable=False, server_default='NGN'),
        sa.Column('status', sa.String(), nullable=False, server_default='initiated'),
        sa.Column('raw_webhook_payload', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_blip_payment_records_order_id', 'blip_payment_records', ['order_id'])
    op.create_index('ix_blip_payment_records_user_id', 'blip_payment_records', ['user_id'])
    op.create_index('ix_blip_payment_records_payment_reference', 'blip_payment_records', ['payment_reference'])
    op.create_index('ix_blip_payment_records_status', 'blip_payment_records', ['status'])

    # 4. create reviews table
    op.create_table(
        'reviews',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('order_id', sa.String(), nullable=False),
        sa.Column('reviewer_id', sa.String(), nullable=False),
        sa.Column('reviewee_id', sa.String(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewer_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewee_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_id')
    )
    op.create_index('ix_reviews_order_id', 'reviews', ['order_id'], unique=True)
    op.create_index('ix_reviews_reviewer_id', 'reviews', ['reviewer_id'])
    op.create_index('ix_reviews_reviewee_id', 'reviews', ['reviewee_id'])

    # 5. create recommended compound indexes
    op.create_index('ix_student_verifications_user_status', 'student_verifications', ['user_id', 'status'])
    op.create_index('ix_transactions_user_created', 'transactions', ['user_id', 'created_at'])


def downgrade() -> None:
    op.drop_index('ix_transactions_user_created', table_name='transactions')
    op.drop_index('ix_student_verifications_user_status', table_name='student_verifications')
    op.drop_table('reviews')
    op.drop_table('blip_payment_records')
    op.drop_table('orders')
    op.drop_table('marketplace_listings')
