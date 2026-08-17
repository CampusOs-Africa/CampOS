import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


def utc_now():
    return datetime.now(UTC)


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        Index("idx_order_buyer_status", "buyer_id", "status"),
        Index("idx_order_seller_status", "seller_id", "status"),
        Index("idx_order_created_status", "created_at", "status"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    buyer_id = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    listing_id = Column(
        String,
        ForeignKey("marketplace_listings.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    seller_id = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    amount = Column(Float, nullable=False)
    payment_reference = Column(String, unique=True, index=True, nullable=False)
    status = Column(
        String, default="initiated", nullable=False, index=True
    )  # 'initiated', 'escrow_locked', 'delivered_pending_release', 'completed', 'refunded', 'disputed', 'cancelled'
    escrow_tx_hash = Column(String, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    buyer = relationship("User", foreign_keys=[buyer_id])
    seller = relationship("User", foreign_keys=[seller_id])
    listing = relationship("MarketplaceListing", back_populates="orders")
    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderItem.created_at",
    )
    review = relationship(
        "Review", back_populates="order", uselist=False, cascade="all, delete-orphan"
    )
    payment_records = relationship(
        "PaymentRecord", back_populates="order", cascade="all, delete-orphan"
    )
    escrow_record = relationship(
        "EscrowRecord", back_populates="order", uselist=False, cascade="all, delete-orphan"
    )

    # Backwards compatibility alias property for blip_records -> payment_records
    @property
    def blip_records(self):
        return self.payment_records


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(
        String, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    listing_id = Column(
        String,
        ForeignKey("marketplace_listings.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    seller_id = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    quantity = Column(Integer, default=1, nullable=False)
    price_per_unit = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    order = relationship("Order", back_populates="items")
    listing = relationship("MarketplaceListing")


class PaymentRecord(Base):
    __tablename__ = "blip_payment_records"
    __table_args__ = (
        Index("idx_payment_order_status", "order_id", "status"),
        Index("idx_payment_user_status", "user_id", "status"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(
        String, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    payment_reference = Column(String, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="NGN", nullable=False)
    provider = Column(String, default="blip_pay", nullable=False)
    status = Column(
        String, default="initiated", nullable=False, index=True
    )  # 'initiated', 'successful', 'failed', 'refunded'
    raw_webhook_payload = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    order = relationship("Order", back_populates="payment_records")
    user = relationship("User", foreign_keys=[user_id])


# Backwards compatibility class alias for BlipPaymentRecord -> PaymentRecord
BlipPaymentRecord = PaymentRecord
