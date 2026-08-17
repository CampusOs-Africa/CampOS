from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user_strict, require_admin
from app.models.user import User
from app.schemas.review import (
    ReviewCreateRequest,
    ReviewModerateRequest,
    ReviewResponse,
)
from app.services.review_service import ReviewService

router = APIRouter(prefix="/reviews", tags=["Reputation & Reviews"])


def get_review_service(db: Session = Depends(get_db)) -> ReviewService:
    return ReviewService(db=db)


@router.post(
    "",
    response_model=ReviewResponse,
    status_code=201,
    summary="Submit peer or marketplace review",
)
@router.post(
    "/",
    response_model=ReviewResponse,
    status_code=201,
    summary="Submit peer or marketplace review",
)
def submit_review(
    body: ReviewCreateRequest,
    service: ReviewService = Depends(get_review_service),
    current_user: User = Depends(get_current_user_strict),
):
    # Reviewer is always derived from the JWT.
    body.reviewer_id = current_user.id
    return service.submit_review(body)

@router.get(
    "/user/{user_id}",
    response_model=list[ReviewResponse],
    summary="Get peer or marketplace reviews received by user",
)
def get_user_reviews(
    user_id: str,
    review_type: str | None = Query(
        None, description="Filter by type ('marketplace', 'peer', or 'all')"
    ),
    status: str = Query("approved", description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: ReviewService = Depends(get_review_service),
):
    # Public reputation profile: reviews a user has received are public.
    return service.get_reviews_by_user(
        user_id=user_id,
        review_type=review_type,
        status=status,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/{review_id}/moderate",
    response_model=ReviewResponse,
    summary="Admin moderate a review",
)
def moderate_review(
    review_id: str,
    body: ReviewModerateRequest,
    service: ReviewService = Depends(get_review_service),
    admin: User = Depends(require_admin),
):
    return service.moderate_review(
        admin_id=admin.id,
        review_id=review_id,
        status=body.status,
        reason=body.reason,
    )


@router.get(
    "/admin/queue",
    response_model=list[ReviewResponse],
    summary="Admin review moderation queue",
)
def get_moderation_queue(
    status: str = Query("flagged", description="Status filter ('flagged', etc.)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: ReviewService = Depends(get_review_service),
    admin: User = Depends(require_admin),
):
    return service.get_moderation_queue(status=status, skip=skip, limit=limit)
