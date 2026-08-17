from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.trust import (
    TrustAnalyticsResponse,
    TrustDashboardResponse,
    TrustHistoryResponse,
    TrustLeaderboardEntryResponse,
)
from app.services.trust_score_service import TrustScoreService

router = APIRouter(prefix="/trust", tags=["Campus Trust Score Engine"])


def get_trust_service(db: Session = Depends(get_db)) -> TrustScoreService:
    return TrustScoreService(db=db)


@router.get(
    "/dashboard/{user_id}",
    response_model=TrustDashboardResponse,
    summary="Get user Trust Score dashboard",
    description="Returns current bounded Trust Score (0–100), badge ('Platinum', 'Gold', etc.), positive/penalty breakdown, and immutable history trail.",
)
def get_trust_dashboard(
    user_id: str,
    service: TrustScoreService = Depends(get_trust_service),
):
    return service.get_trust_dashboard(user_id=user_id)


@router.get(
    "/leaderboard",
    response_model=list[TrustLeaderboardEntryResponse],
    summary="Get campus Trust Score leaderboard",
    description="Returns top trusted students across campus filterable by school, department, and role.",
)
def get_trust_leaderboard(
    school: str | None = Query(None, description="Filter by school or institution"),
    department: str | None = Query(None, description="Filter by department"),
    role: str | None = Query("student", description="Filter by role ('student', etc.)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: TrustScoreService = Depends(get_trust_service),
):
    return service.get_leaderboard(
        school=school,
        department=department,
        role=role,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/history/{user_id}",
    response_model=list[TrustHistoryResponse],
    summary="Get immutable Trust Score audit trail for user",
    description="Returns chronological audit trail of all Trust Score reward and penalty events.",
)
def get_trust_history(
    user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: TrustScoreService = Depends(get_trust_service),
):
    return service.get_trust_history(user_id=user_id, skip=skip, limit=limit)


@router.get(
    "/analytics",
    response_model=TrustAnalyticsResponse,
    summary="Get campus-wide Trust Score analytics",
    description="Returns average campus score, verified student count, 24h event count, and score tier distribution.",
)
def get_campus_trust_analytics(
    service: TrustScoreService = Depends(get_trust_service),
):
    return service.get_campus_analytics()
