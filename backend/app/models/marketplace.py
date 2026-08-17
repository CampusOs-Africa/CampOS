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
    Text,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


def utc_now():
    return datetime.now(UTC)


class MarketplaceCategory(Base):
    __tablename__ = "marketplace_categories"

    id = Column(String, primary_key=True)  # slug e.g. 'books', 'electronics'
    name = Column(String, nullable=False, unique=True, index=True)
    description = Column(String, nullable=True)
    icon = Column(String, nullable=True)
    active_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class MarketplaceListing(Base):
    __tablename__ = "marketplace_listings"
    __table_args__ = (
        Index("idx_listing_cat_status", "category", "status"),
        Index("idx_listing_seller_status", "seller_id", "status"),
        Index("idx_listing_created_status", "created_at", "status"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    seller_id = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    category = Column(
        String,
        ForeignKey("marketplace_categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )  # 'books', 'electronics', 'accommodation', 'tutoring', 'tickets', 'services'
    price = Column(Float, nullable=False)
    condition = Column(
        String, default="good", nullable=False
    )  # 'new', 'like_new', 'good', 'fair', 'poor'
    images = Column(
        JSON, nullable=False
    )  # ARRAY of Cloudinary image URL strings
    status = Column(
        String, default="active", nullable=False, index=True
    )  # 'active', 'pending_order', 'sold', 'suspended'
    inventory_count = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    seller = relationship("User", foreign_keys=[seller_id])
    orders = relationship(
        "Order",
        back_populates="listing",
        cascade="all, delete-orphan",
        order_by="desc(Order.created_at)",
    )
