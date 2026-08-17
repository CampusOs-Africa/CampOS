import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


def utc_now():
    return datetime.now(UTC)


class TrustHistory(Base):
    __tablename__ = "trust_history"
    __table_args__ = (
        Index("idx_trust_history_user_created", "user_id", "created_at"),
        Index("idx_trust_history_event_type", "event_type", "created_at"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    delta = Column(
        Integer, nullable=False
    )  # e.g. +10, +5, +2, +1, -5, -10, -20
    old_score = Column(Integer, nullable=False)
    new_score = Column(Integer, nullable=False)
    event_type = Column(
        String, nullable=False, index=True
    )  # 'verification', 'order_release', 'peer_review', 'marketplace_review', 'wallet_p2p', 'fraud_penalty', 'dispute_lost', 'order_refund', 'review_moderation'
    reason = Column(Text, nullable=False)
    reference_id = Column(String, nullable=True, index=True)
    created_at = Column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    user = relationship("User", foreign_keys=[user_id])
