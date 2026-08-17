import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, String, Text

from app.core.database import Base


def utc_now():
    return datetime.now(UTC)


class AdminAuditLog(Base):
    """Append-only traceability record for sensitive admin operations."""

    __tablename__ = "admin_audit_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    admin_id = Column(String, nullable=False, index=True)
    action = Column(String, nullable=False, index=True)
    target_type = Column(String, nullable=True)
    target_id = Column(String, nullable=True, index=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "admin_id": self.admin_id,
            "action": self.action,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "reason": self.reason,
            "created_at": self.created_at,
        }
