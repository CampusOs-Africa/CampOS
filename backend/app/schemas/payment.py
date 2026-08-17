from datetime import datetime

from pydantic import BaseModel, Field


class InitiatePaymentRequest(BaseModel):
    listing_id: str
    # Optional client-supplied idempotency key; server also derives one if absent.
    idempotency_key: str | None = Field(default=None, max_length=128)


class PaymentIntentResponse(BaseModel):
    id: str
    order_id: str
    display_price: str | None = None
    display_currency: str | None = None
    settlement_asset: str | None = None
    settlement_amount_wei: str | None = None
    order_id_hex: str | None = None
    amount_minor: int
    currency: str
    provider: str
    status: str
    checkout_url: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaymentStatusResponse(BaseModel):
    id: str
    order_id: str
    order_id_hex: str | None = None
    status: str
    amount_minor: int
    currency: str
    provider_reference: str | None = None
    quai_tx_hash: str | None = None
    failure_reason: str | None = None
    paid_at: datetime | None = None

    model_config = {"from_attributes": True}
