import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


def utc_now():
    return datetime.now(UTC)


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        Index("idx_tx_user_created", "user_id", "created_at"),
        Index("idx_tx_wallet_created", "wallet_address", "created_at"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    wallet_address = Column(String, nullable=False, index=True)
    recipient_address = Column(String, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    tx_hash = Column(String, nullable=False, unique=True, index=True)
    type = Column(
        String, default="send", nullable=False, index=True
    )  # 'send', 'receive', 'deposit', 'withdraw', 'faucet'
    status = Column(
        String, default="confirmed", nullable=False, index=True
    )  # 'pending', 'confirmed', 'failed'
    network = Column(String, default="Quai Network Testnet", nullable=False)
    block_number = Column(Integer, nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    user = relationship("User", foreign_keys=[user_id])
