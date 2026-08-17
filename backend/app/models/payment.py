import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class PaymentIntent(Base):
    """Server-authoritative payment record.

    Amounts are stored as integer minor units (e.g. kobo for NGN) to avoid
    floating-point errors for money. The client never supplies amount, buyer,
    seller, or status.
    """

    __tablename__ = "payment_intents"
    __table_args__ = (
        UniqueConstraint("idempotency_key", "buyer_id", name="uq_payment_idempotency_buyer"),
        Index("ix_payment_intent_order", "order_id"),
        Index("ix_payment_intent_status", "status"),
        Index("ix_payment_intent_provider_ref", "provider", "provider_reference"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(
        String, ForeignKey("orders.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    buyer_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    seller_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Display price/currency from the listing (e.g. NGN). This is the
    # user-facing price only and is NOT the on-chain amount until a verified
    # NGN->QUAI quote provider exists.
    display_price = Column(String, nullable=True)
    display_currency = Column(String, nullable=True)

    # On-chain settlement: native QUAI, amount in wei (decimal string to
    # support 256-bit EVM values portably).
    settlement_asset = Column(String, nullable=True)
    settlement_amount_wei = Column(String, nullable=True)

    # Legacy fields retained for backwards compatibility.
    amount_minor = Column(String, nullable=False)  # == settlement_amount_wei
    currency = Column(String, default="NGN", nullable=False)  # display currency

    provider = Column(String, default="blip_pay", nullable=False)
    provider_reference = Column(String, nullable=True, index=True)
    checkout_url = Column(String, nullable=True)

    # pending -> processing -> paid | failed | cancelled | expired ; paid -> refunded
    status = Column(String, default="pending", nullable=False, index=True)
    idempotency_key = Column(String, nullable=False)

    quai_tx_hash = Column(String, nullable=True)
    failure_reason = Column(String, nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )


class WebhookEvent(Base):
    """Persistent record of provider webhook events for replay/idempotency."""

    __tablename__ = "webhook_events"
    __table_args__ = (
        UniqueConstraint("provider", "event_id", name="uq_webhook_provider_event"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    provider = Column(String, nullable=False, index=True)
    event_id = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=True)
    payment_reference = Column(String, nullable=True, index=True)
    signature_verified = Column(Boolean, nullable=False, default=False)
    payload_hash = Column(String, nullable=True)
    status = Column(String, default="received", nullable=False)
    processing_error = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
