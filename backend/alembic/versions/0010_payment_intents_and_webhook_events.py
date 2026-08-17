"""Payment intents and webhook events.

Revision ID: 0010
Revises: 0009
Create Date: 2026-08-16 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "payment_intents",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("order_id", sa.String(), nullable=False),
        sa.Column("buyer_id", sa.String(), nullable=False),
        sa.Column("seller_id", sa.String(), nullable=False),
        sa.Column("amount_minor", sa.String(), nullable=False),
        sa.Column("currency", sa.String(), nullable=False, server_default="NGN"),
        sa.Column("provider", sa.String(), nullable=False, server_default="blip_pay"),
        sa.Column("provider_reference", sa.String(), nullable=True),
        sa.Column("checkout_url", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("idempotency_key", sa.String(), nullable=False),
        sa.Column("quai_tx_hash", sa.String(), nullable=True),
        sa.Column("failure_reason", sa.String(), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["buyer_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["seller_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key", "buyer_id", name="uq_payment_idempotency_buyer"),
    )
    op.create_index("ix_payment_intent_order", "payment_intents", ["order_id"])
    op.create_index("ix_payment_intent_status", "payment_intents", ["status"])
    op.create_index(
        "ix_payment_intent_provider_ref",
        "payment_intents",
        ["provider", "provider_reference"],
    )

    op.create_table(
        "webhook_events",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("event_id", sa.String(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=True),
        sa.Column("payment_reference", sa.String(), nullable=True),
        sa.Column("signature_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("payload_hash", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="received"),
        sa.Column("processing_error", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "event_id", name="uq_webhook_provider_event"),
    )
    op.create_index("ix_webhook_events_provider", "webhook_events", ["provider"])
    op.create_index("ix_webhook_events_event_id", "webhook_events", ["event_id"])
    op.create_index(
        "ix_webhook_events_payment_ref", "webhook_events", ["payment_reference"]
    )


def downgrade() -> None:
    op.drop_index("ix_webhook_events_payment_ref", table_name="webhook_events")
    op.drop_index("ix_webhook_events_event_id", table_name="webhook_events")
    op.drop_index("ix_webhook_events_provider", table_name="webhook_events")
    op.drop_table("webhook_events")
    op.drop_index("ix_payment_intent_provider_ref", table_name="payment_intents")
    op.drop_index("ix_payment_intent_status", table_name="payment_intents")
    op.drop_index("ix_payment_intent_order", table_name="payment_intents")
    op.drop_table("payment_intents")
