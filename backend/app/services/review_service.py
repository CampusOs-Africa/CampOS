from sqlalchemy.orm import Session

from app.core.exceptions import CampusOSException, EntityNotFoundError, ForbiddenError
from app.models.review import Review
from app.models.user import User
from app.repositories.order_repository import OrderRepository
from app.repositories.review_repository import ReviewRepository
from app.repositories.user_repository import UserRepository
from app.schemas.review import ReviewCreateRequest, ReviewResponse
from app.services.trust_service import TrustService


class ReviewService:
    def __init__(self, db: Session):
        self.db = db
        self.review_repo = ReviewRepository(db)
        self.order_repo = OrderRepository(db)
        self.user_repo = UserRepository(db)
        self.trust_service = TrustService(db)

    def _enrich_review(self, review: Review) -> ReviewResponse:
        return self._enrich_reviews([review])[0]

    def _enrich_reviews(self, reviews: list[Review]) -> list[ReviewResponse]:
        if not reviews:
            return []
        reviewer_ids = list({r.reviewer_id for r in reviews})
        reviewee_ids = list({r.reviewee_id for r in reviews})
        all_user_ids = list(set(reviewer_ids + reviewee_ids))

        users = self.db.query(User).filter(User.id.in_(all_user_ids)).all()
        user_map = {u.id: u.name for u in users}

        res_list = []
        for r in reviews:
            res = ReviewResponse.model_validate(r)
            res.reviewer_name = user_map.get(r.reviewer_id)
            res.reviewee_name = user_map.get(r.reviewee_id)
            res_list.append(res)
        return res_list

    def submit_review(self, req: ReviewCreateRequest) -> ReviewResponse:
        reviewer = self.user_repo.get_by_id(req.reviewer_id)
        if not reviewer:
            raise EntityNotFoundError("User", req.reviewer_id)

        reviewee = self.user_repo.get_by_id(req.reviewee_id)
        if not reviewee:
            raise EntityNotFoundError("User", req.reviewee_id)

        if req.reviewer_id == req.reviewee_id:
            raise CampusOSException(
                "You cannot submit a review for yourself.",
                status_code=400,
            )

        review_type = (req.review_type or "marketplace").lower()
        order_id_to_store = None

        if review_type == "marketplace":
            if not req.order_id:
                raise CampusOSException(
                    "Marketplace reviews require a valid order_id.",
                    status_code=400,
                )
            order = self.order_repo.get_by_id(req.order_id)
            if not order:
                raise EntityNotFoundError("Order", req.order_id)

            if order.status != "completed":
                raise CampusOSException(
                    "You can only submit a review after the order escrow has been completed and released.",
                    status_code=400,
                )

            if req.reviewer_id not in (order.buyer_id, order.seller_id):
                raise ForbiddenError(
                    "Only participants of this order can submit a review."
                )

            existing = self.review_repo.get_by_order_id(req.order_id)
            if existing:
                raise CampusOSException(
                    f"A review has already been submitted for order {req.order_id}.",
                    status_code=409,
                )
            order_id_to_store = req.order_id

        review = Review(
            order_id=order_id_to_store,
            reviewer_id=req.reviewer_id,
            reviewee_id=req.reviewee_id,
            rating=req.rating,
            comment=req.comment,
            review_type=review_type,
            status="approved",
        )
        created = self.review_repo.create(review)

        # Award +2 Trust Score for positive marketplace review (>=4 stars) or +1 for peer review
        ref_id = req.order_id if req.order_id else created.id
        self.trust_service.award_review_bonus(
            req.reviewee_id,
            req.rating,
            ref_id,
            review_type=review_type,
        )

        return self._enrich_review(created)

    def moderate_review(
        self, admin_id: str, review_id: str, status: str, reason: str
    ) -> ReviewResponse:
        admin = self.user_repo.get_by_id(admin_id)
        if not admin or admin.role != "admin":
            raise ForbiddenError("Only administrators can moderate reviews.")

        review = self.review_repo.get_by_id(review_id)
        if not review:
            raise EntityNotFoundError("Review", review_id)

        old_status = review.status
        review.status = status.lower()
        review.moderated_by = admin_id
        review.moderation_reason = reason
        updated = self.review_repo.update(review)

        if old_status == "approved" and review.status in ("flagged", "removed"):
            self.trust_service.penalize_review_removed(
                review.reviewee_id,
                review.rating,
                review.id,
                review_type=review.review_type,
            )

        return self._enrich_review(updated)

    def get_reviews_by_user(
        self,
        user_id: str,
        review_type: str | None = None,
        status: str = "approved",
        skip: int = 0,
        limit: int = 20,
    ) -> list[ReviewResponse]:
        reviews = self.review_repo.get_by_reviewee(
            user_id,
            review_type=review_type,
            status=status,
            skip=skip,
            limit=limit,
        )
        return self._enrich_reviews(reviews)

    def get_moderation_queue(
        self, status: str = "flagged", skip: int = 0, limit: int = 50
    ) -> list[ReviewResponse]:
        reviews = self.review_repo.get_moderation_queue(
            status=status, skip=skip, limit=limit
        )
        return self._enrich_reviews(reviews)
