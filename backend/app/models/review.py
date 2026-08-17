import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


def utc_now():
    return datetime.now(UTC)


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        Index("idx_review_reviewee_rating", "reviewee_id", "rating"),
        Index("idx_review_reviewee_type_status", "reviewee_id", "review_type", "status"),
        Index("idx_review_reviewer_type", "reviewer_id", "review_type"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(
        String,
        ForeignKey("orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    reviewer_id = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reviewee_id = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rating = Column(Integer, nullable=False)  # 1 to 5
    comment = Column(Text, nullable=True)
    review_type = Column(String, default="marketplace", nullable=False, index=True)  # 'marketplace', 'peer'
    status = Column(String, default="approved", nullable=False, index=True)  # 'approved', 'flagged', 'removed'
    moderated_by = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    moderation_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    order = relationship("Order", back_populates="review")
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    reviewee = relationship("User", foreign_keys=[reviewee_id])
    moderator = relationship("User", foreign_keys=[moderated_by])
