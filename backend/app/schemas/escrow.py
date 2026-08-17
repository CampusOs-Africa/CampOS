from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EscrowCreateRequest(BaseModel):
    order_id: str = Field(..., description="UUID of the order")
    buyer_id: str = Field(..., description="UUID of the buyer")
    seller_id: str = Field(..., description="UUID of the seller")
    amount: float = Field(..., gt=0, description="Amount in QUAI / NGN")


class EscrowActionRequest(BaseModel):
    order_id: str = Field(..., description="UUID of the order")
    actor_id: str = Field(..., description="UUID of the actor (buyer, seller, or admin)")
    reason: str | None = Field(None, description="Reason for refund or dispute")


class EscrowRecordResponse(BaseModel):
    id: str
    order_id: str
    buyer_id: str
    seller_id: str
    amount: float
    state: str
    quai_order_id: str
    escrow_tx_hash: str | None = None
    expires_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
