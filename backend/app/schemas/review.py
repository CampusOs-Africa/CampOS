from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReviewCreateRequest(BaseModel):
    order_id: str | None = Field(
        None, description="UUID of the completed order (optional for peer reviews)"
    )
    # reviewer_id is populated by the backend from the JWT and is ignored if
    # supplied by the client.
    reviewer_id: str | None = Field(
        None, description="UUID of the person submitting the review (set by backend)"
    )
    reviewee_id: str = Field(..., description="UUID of the person being reviewed")
    rating: int = Field(..., ge=1, le=5, description="Star rating from 1 to 5")
    comment: str | None = Field(None, max_length=1000)
    review_type: str = Field(
        "marketplace", description="'marketplace' or 'peer'"
    )


class ReviewModerateRequest(BaseModel):
    status: str = Field(
        ..., description="'approved', 'flagged', or 'removed'"
    )
    reason: str = Field(
        ..., min_length=3, max_length=500, description="Explanation for moderation"
    )


class ReviewResponse(BaseModel):
    id: str
    order_id: str | None = None
    reviewer_id: str
    reviewee_id: str
    rating: int
    comment: str | None = None
    review_type: str = "marketplace"
    status: str = "approved"
    moderated_by: str | None = None
    moderation_reason: str | None = None
    created_at: datetime
    reviewer_name: str | None = None
    reviewee_name: str | None = None

    model_config = ConfigDict(from_attributes=True)
