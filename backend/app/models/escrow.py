import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import Base


def utc_now():
    return datetime.now(UTC)


class EscrowRecord(Base):
    __tablename__ = "escrow_records"
    __table_args__ = (
        Index("idx_escrow_buyer_state", "buyer_id", "state"),
        Index("idx_escrow_seller_state", "seller_id", "state"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(
        String,
        ForeignKey("orders.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    buyer_id = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    seller_id = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    amount = Column(Float, nullable=False)
    state = Column(
        String, default="CREATED", nullable=False, index=True
    )  # 'CREATED', 'FUNDED', 'COMPLETED', 'REFUNDED', 'CANCELLED', 'DISPUTED'
    quai_order_id = Column(String, nullable=False, index=True)
    escrow_tx_hash = Column(String, nullable=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    order = relationship("Order", back_populates="escrow_record")
    buyer = relationship("User", foreign_keys=[buyer_id])
    seller = relationship("User", foreign_keys=[seller_id])
