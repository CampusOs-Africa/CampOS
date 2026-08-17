import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


def utc_now():
    return datetime.now(UTC)

class StudentVerification(Base):
    __tablename__ = "student_verifications"
    __table_args__ = (
        Index("idx_verif_user_status", "user_id", "status"),
        Index("idx_verif_created_status", "created_at", "status"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id_url = Column(String, nullable=False)
    admission_letter_url = Column(String, nullable=False)
    university_email = Column(String, nullable=False, index=True)
    status = Column(String, default="pending", nullable=False, index=True)  # pending, approved, rejected, resubmission_requested, revoked
    approved_by = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    credential_hash = Column(String, nullable=True, index=True)
    tx_hash = Column(String, nullable=True, index=True)  # Stored Quai Network transaction receipt hash
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="verifications", foreign_keys=[user_id])
    admin = relationship("User", foreign_keys=[approved_by])
    history = relationship(
        "VerificationHistory",
        back_populates="verification",
        cascade="all, delete-orphan",
        order_by="desc(VerificationHistory.timestamp)",
    )


class VerificationHistory(Base):
    __tablename__ = "verification_history"
    __table_args__ = (
        Index("idx_history_user_time", "user_id", "timestamp"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    verification_id = Column(String, ForeignKey("student_verifications.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    old_status = Column(String, nullable=True)
    new_status = Column(String, nullable=False)
    changed_by = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reason = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    verification = relationship("StudentVerification", back_populates="history")
    actor = relationship("User", foreign_keys=[changed_by])
