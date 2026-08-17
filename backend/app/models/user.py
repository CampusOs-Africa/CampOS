import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, Index, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


def utc_now():
    return datetime.now(UTC)

class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("idx_user_verif_trust", "verification_status", "trust_score"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    date_of_birth = Column(String, nullable=True)  # ISO date string (YYYY-MM-DD)
    gender = Column(String, nullable=True)
    wallet_address = Column(String, unique=True, index=True, nullable=True)

    # Legacy student identifier (free text). New academic profile fields below.
    student_id = Column(String, nullable=True)
    school = Column(String, nullable=True)
    faculty = Column(String, nullable=True)
    department = Column(String, nullable=True)
    level = Column(String, nullable=True)
    matric_number = Column(String, nullable=True)
    admission_year = Column(String, nullable=True)  # e.g. "2023"
    school_email = Column(String, nullable=True)

    trust_score = Column(Integer, default=50, nullable=False)
    verification_status = Column(String, default="pending", nullable=False)
    role = Column(String, default="student", nullable=False)

    # Authentication: PBKDF2-HMAC-SHA256 password hash (nullable to preserve
    # legacy/seeded accounts that authenticate via one-click demo flows).
    hashed_password = Column(String, nullable=True)
    # Account status for admin suspension/deactivation.
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    verifications = relationship("StudentVerification", back_populates="user", foreign_keys="StudentVerification.user_id", cascade="all, delete-orphan")
