from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FraudReportCreateRequest(BaseModel):
    reporter_id: str = Field(..., description="UUID of reporting user")
    reported_user_id: str = Field(..., description="UUID of reported user")
    category: str = Field(
        ...,
        description="'scam_listing', 'fake_item', 'non_delivery', 'identity_fraud', 'other'",
    )
    description: str = Field(..., min_length=10, max_length=2000)
    evidence_url: str | None = Field(
        None, description="Cloudinary evidence image or PDF URL"
    )
    order_id: str | None = Field(
        None, description="Optional associated marketplace order UUID"
    )


class FraudReportResolveRequest(BaseModel):
    status: str = Field(..., description="'resolved_confirmed' or 'resolved_dismissed'")
    penalty_points: int = Field(
        20, ge=0, le=50, description="Points to deduct if confirmed fraud"
    )
    resolution_notes: str = Field(..., min_length=5, max_length=1000)


class FraudReportResponse(BaseModel):
    id: str
    reporter_id: str
    reported_user_id: str
    category: str
    description: str
    evidence_url: str | None = None
    order_id: str | None = None
    status: str
    admin_id: str | None = None
    resolution_notes: str | None = None
    penalty_applied: int = 0
    created_at: datetime
    resolved_at: datetime | None = None
    reporter_name: str | None = None
    reported_user_name: str | None = None

    model_config = ConfigDict(from_attributes=True)
