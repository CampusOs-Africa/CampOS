from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TrustHistoryResponse(BaseModel):
    id: str
    user_id: str
    delta: int
    old_score: int
    new_score: int
    event_type: str
    reason: str
    reference_id: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TrustLeaderboardEntryResponse(BaseModel):
    user_id: str
    name: str
    email: str
    school: str | None = None
    department: str | None = None
    trust_score: int
    trust_badge: str
    is_verified: bool
    rank: int = 0

    model_config = ConfigDict(from_attributes=True)


class TrustAnalyticsResponse(BaseModel):
    campus_average_score: float
    total_verified_students: int
    score_distribution: dict[str, int]
    recent_trust_events_24h: int


class TrustDashboardResponse(BaseModel):
    user_id: str
    name: str
    email: str
    verification_status: str
    trust_score: int
    trust_badge: str
    history: list[TrustHistoryResponse]
    total_positive_earned: int
    total_penalties_deducted: int
    completed_sales: int
    peer_reviews_count: int
    average_rating: float

    model_config = ConfigDict(from_attributes=True)
