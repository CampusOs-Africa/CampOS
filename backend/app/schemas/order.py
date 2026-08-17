from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class OrderCreateRequest(BaseModel):
    buyer_id: str = Field(..., description="UUID of the buyer")
    listing_id: str = Field(..., description="UUID of the marketplace listing")
    amount: float = Field(..., gt=0, description="Agreed purchase amount")
    quantity: int = Field(1, ge=1, le=100, description="Quantity of items purchased")


class OrderItemResponse(BaseModel):
    id: str
    order_id: str
    listing_id: str
    seller_id: str
    quantity: int
    price_per_unit: float
    subtotal: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    id: str
    buyer_id: str
    listing_id: str
    seller_id: str
    amount: float
    payment_reference: str
    status: str
    escrow_tx_hash: str | None = None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    listing_title: str | None = None
    buyer_name: str | None = None
    seller_name: str | None = None
    items: list[OrderItemResponse] | None = None

    model_config = ConfigDict(from_attributes=True)


class BlipPayInitiateResponse(BaseModel):
    order_id: str
    payment_reference: str
    payment_url: str
    amount: float
    currency: str = "NGN"
    status: str = "initiated"


class BlipPayWebhookPayload(BaseModel):
    payment_reference: str = Field(..., description="Unique Blip Pay order reference")
    status: str = Field("success", description="Payment status ('success', 'failed')")
    transaction_id: str | None = None
    amount: float | None = None
    raw_data: dict[str, Any] | None = None


class BlipPaymentRecordResponse(BaseModel):
    id: str
    order_id: str
    user_id: str
    payment_reference: str
    amount: float
    currency: str
    provider: str = "blip_pay"
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderDisputeRequest(BaseModel):
    reason: str = Field(..., min_length=5, description="Explanation for disputing order")
