from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MarketplaceCategoryResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    icon: str | None = None
    active_count: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MarketplaceListingCreate(BaseModel):
    seller_id: str | None = None
    title: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=5, max_length=2000)
    category: str = Field(
        ...,
        description="books|electronics|accommodation|tutoring|tickets|services",
    )
    price: float = Field(..., gt=0)
    condition: str = Field(
        "good", description="new|like_new|good|fair|poor"
    )
    inventory_count: int = Field(1, ge=1, le=100)
    images: list[str] = Field(..., min_length=1, description="ARRAY of Cloudinary URL strings")


class MarketplaceListingUpdate(BaseModel):
    title: str | None = Field(None, min_length=3, max_length=100)
    description: str | None = Field(None, min_length=5, max_length=2000)
    category: str | None = None
    price: float | None = Field(None, gt=0)
    condition: str | None = None
    inventory_count: int | None = Field(None, ge=0, le=100)
    images: list[str] | None = None
    status: str | None = None


class MarketplaceListingResponse(BaseModel):
    id: str
    seller_id: str | None = None
    title: str
    description: str
    category: str
    price: float
    condition: str
    images: list[str]
    status: str
    inventory_count: int
    created_at: datetime
    updated_at: datetime
    seller_name: str | None = None
    seller_trust_score: int | None = None
    seller_verified: bool | None = None

    model_config = ConfigDict(from_attributes=True)


class SellerProfileResponse(BaseModel):
    user_id: str
    name: str
    email: str
    trust_score: int
    is_verified: bool
    active_listings_count: int
    total_sales_count: int
    average_rating: float
    reviews: list[Any] = []

    model_config = ConfigDict(from_attributes=True)
