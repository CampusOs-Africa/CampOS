from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.review import Review


class ReviewRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, review: Review) -> Review:
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        return review

    def get_by_id(self, review_id: str) -> Review | None:
        return self.db.query(Review).filter(Review.id == review_id).first()

    def get_by_order_id(self, order_id: str) -> Review | None:
        return (
            self.db.query(Review)
            .filter(Review.order_id == order_id)
            .first()
        )

    def update(self, review: Review) -> Review:
        self.db.commit()
        self.db.refresh(review)
        return review

    def get_by_reviewee(
        self,
        user_id: str,
        review_type: str | None = None,
        status: str = "approved",
        skip: int = 0,
        limit: int = 20,
    ) -> list[Review]:
        query = self.db.query(Review).filter(
            Review.reviewee_id == user_id, Review.status == status
        )
        if review_type and review_type.lower() != "all":
            query = query.filter(Review.review_type == review_type.lower())
        return (
            query.order_by(Review.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_average_rating(self, reviewee_id: str) -> tuple[float, int]:
        result = (
            self.db.query(
                func.avg(Review.rating).label("avg_rating"),
                func.count(Review.id).label("total_reviews"),
            )
            .filter(
                Review.reviewee_id == reviewee_id,
                Review.status == "approved",
            )
            .first()
        )
        if not result or result.total_reviews == 0:
            return 0.0, 0
        return round(float(result.avg_rating or 0.0), 2), int(
            result.total_reviews or 0
        )

    def get_moderation_queue(
        self, status: str = "flagged", skip: int = 0, limit: int = 50
    ) -> list[Review]:
        return (
            self.db.query(Review)
            .filter(Review.status == status)
            .order_by(Review.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
