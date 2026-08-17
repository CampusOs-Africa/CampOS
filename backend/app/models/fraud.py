import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


def utc_now():
    return datetime.now(UTC)


class FraudReport(Base):
    __tablename__ = "fraud_reports"
    __table_args__ = (
        Index("idx_fraud_reported_status", "reported_user_id", "status"),
        Index("idx_fraud_reporter_created", "reporter_id", "created_at"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    reporter_id = Column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reported_user_id = Column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category = Column(
        String, nullable=False, index=True
    )  # 'scam_listing', 'fake_item', 'non_delivery', 'identity_fraud', 'other'
    description = Column(Text, nullable=False)
    evidence_url = Column(String, nullable=True)  # Cloudinary URL proof
    order_id = Column(
        String,
        ForeignKey("orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status = Column(
        String, default="pending", nullable=False, index=True
    )  # 'pending', 'investigating', 'resolved_confirmed', 'resolved_dismissed'
    admin_id = Column(
        String,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    resolution_notes = Column(Text, nullable=True)
    penalty_applied = Column(Integer, default=0, nullable=False)  # e.g. -20
    created_at = Column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    reporter = relationship("User", foreign_keys=[reporter_id])
    reported_user = relationship("User", foreign_keys=[reported_user_id])
    order = relationship("Order", foreign_keys=[order_id])
    admin = relationship("User", foreign_keys=[admin_id])
