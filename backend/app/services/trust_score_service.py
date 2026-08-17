import logging

from sqlalchemy.orm import Session

from app.core.exceptions import EntityNotFoundError
from app.core.logger import log_audit_event
from app.models.trust import TrustHistory
from app.repositories.order_repository import OrderRepository
from app.repositories.review_repository import ReviewRepository
from app.repositories.trust_repository import TrustRepository
from app.repositories.user_repository import UserRepository
from app.schemas.trust import (
    TrustAnalyticsResponse,
    TrustDashboardResponse,
    TrustHistoryResponse,
    TrustLeaderboardEntryResponse,
)

logger = logging.getLogger("campusos.trust")


class TrustScoreService:
    """
    CampusOS Milestone 6 Bounded Trust Score Engine (0–100 range, baseline 50).
    Every score change generates an immutable audit record in TrustHistory.
    """

    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.trust_repo = TrustRepository(db)
        self.order_repo = OrderRepository(db)
        self.review_repo = ReviewRepository(db)

    def _clamp_score(self, score: int) -> int:
        return max(0, min(100, score))

    def get_trust_badge(self, score: int) -> str:
        if score >= 85:
            return "Platinum"
        if score >= 70:
            return "Gold"
        if score >= 55:
            return "Silver"
        if score >= 40:
            return "Bronze"
        return "At-Risk"

    def update_user_score(
        self,
        user_id: str,
        delta: int,
        reason: str,
        event_type: str = "general",
        reference_id: str | None = None,
    ) -> int:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise EntityNotFoundError("User", user_id)

        old_score = user.trust_score
        new_score = self._clamp_score(old_score + delta)
        user.trust_score = new_score
        self.user_repo.update(user)

        # Create immutable audit record
        history = TrustHistory(
            user_id=user_id,
            delta=delta,
            old_score=old_score,
            new_score=new_score,
            event_type=event_type,
            reason=reason,
            reference_id=reference_id,
        )
        self.trust_repo.create_history(history)

        log_audit_event(
            action="TRUST_SCORE_UPDATED",
            actor_id=user_id,
            target_id=user_id,
            status="SUCCESS",
            details={
                "old_score": old_score,
                "new_score": new_score,
                "delta": delta,
                "event_type": event_type,
                "reason": reason,
                "reference_id": reference_id,
            },
        )
        logger.info(
            f"Trust Score updated for user {user_id}: {old_score} -> {new_score} (Delta: {delta:+d}, Type: '{event_type}', Reason: '{reason}')"
        )
        return user.trust_score

    def award_verification_bonus(
        self, user_id: str, verification_id: str | None = None
    ) -> int:
        """Award +10 Trust Score for verified student identity."""
        return self.update_user_score(
            user_id=user_id,
            delta=10,
            reason="Approved Verified Student Identity",
            event_type="verification",
            reference_id=verification_id,
        )

    def award_order_completion_bonus(
        self, buyer_id: str, seller_id: str, order_id: str
    ) -> tuple[int, int]:
        """Award +5 Trust Score to Buyer and +5 to Seller upon successful escrow release."""
        buyer_new = self.update_user_score(
            buyer_id,
            5,
            f"Completed marketplace order {order_id} (Buyer bonus)",
            event_type="order_release",
            reference_id=order_id,
        )
        seller_new = self.update_user_score(
            seller_id,
            5,
            f"Completed marketplace order {order_id} (Seller bonus)",
            event_type="order_release",
            reference_id=order_id,
        )
        return buyer_new, seller_new

    def award_review_bonus(
        self,
        reviewee_id: str,
        rating: int,
        review_id: str,
        review_type: str = "marketplace",
    ) -> int | None:
        """Award +2 Trust Score for positive marketplace review (4 or 5 stars) or +1 for peer review."""
        if rating >= 4:
            delta = 2 if review_type == "marketplace" else 1
            return self.update_user_score(
                reviewee_id,
                delta,
                f"Received positive {rating}-star {review_type} review",
                event_type=f"{review_type}_review",
                reference_id=review_id,
            )
        return None

    def penalize_review_removed(
        self, reviewee_id: str, rating: int, review_id: str, review_type: str = "marketplace"
    ) -> int | None:
        """Reverse trust bonus when a positive review is removed by an admin moderator."""
        if rating >= 4:
            delta = -2 if review_type == "marketplace" else -1
            return self.update_user_score(
                reviewee_id,
                delta,
                f"Positive {review_type} review {review_id} removed by moderator",
                event_type="review_moderation",
                reference_id=review_id,
            )
        return None

    def award_wallet_reputation(
        self, user_id: str, reason: str, reference_id: str | None = None
    ) -> int:
        """Award +5 Trust Score for Quai wallet welcome or verified P2P activity."""
        return self.update_user_score(
            user_id=user_id,
            delta=5,
            reason=reason,
            event_type="wallet_p2p",
            reference_id=reference_id,
        )

    def penalize_order_refund(
        self, seller_id: str, order_id: str
    ) -> int:
        """Deduct -5 Trust Score from Seller on order refund."""
        return self.update_user_score(
            seller_id,
            -5,
            f"Order {order_id} refunded to buyer",
            event_type="order_refund",
            reference_id=order_id,
        )

    def penalize_dispute_lost(
        self, user_id: str, order_id: str, penalty: int = -10
    ) -> int:
        """Deduct penalty points (-10 default) when an escrow dispute is ruled against a user."""
        return self.update_user_score(
            user_id,
            penalty,
            f"Escrow dispute for order {order_id} ruled against user",
            event_type="dispute_lost",
            reference_id=order_id,
        )

    def penalize_fraud_report(
        self,
        user_id: str,
        reason: str,
        penalty: int = -20,
        report_id: str | None = None,
    ) -> int:
        """Deduct penalty points on confirmed scam/fraud activity."""
        return self.update_user_score(
            user_id,
            penalty,
            f"Confirmed fraud report: {reason}",
            event_type="fraud_penalty",
            reference_id=report_id,
        )

    def get_trust_dashboard(self, user_id: str) -> TrustDashboardResponse:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise EntityNotFoundError("User", user_id)

        history_rows = self.trust_repo.get_history_by_user_id(
            user_id, skip=0, limit=20
        )
        history = [
            TrustHistoryResponse.model_validate(h) for h in history_rows
        ]

        total_pos = sum(h.delta for h in history_rows if h.delta > 0)
        total_pen = sum(abs(h.delta) for h in history_rows if h.delta < 0)

        completed_sales = self.order_repo.count_by_seller(
            user_id, status="completed"
        )
        peer_reviews = self.review_repo.get_by_reviewee(
            user_id, review_type="all", status="approved", skip=0, limit=1000
        )
        avg_rating, _ = self.review_repo.get_average_rating(user_id)

        return TrustDashboardResponse(
            user_id=user.id,
            name=user.name,
            email=user.email,
            verification_status=user.verification_status,
            trust_score=user.trust_score,
            trust_badge=self.get_trust_badge(user.trust_score),
            history=history,
            total_positive_earned=total_pos,
            total_penalties_deducted=total_pen,
            completed_sales=completed_sales,
            peer_reviews_count=len(peer_reviews),
            average_rating=avg_rating,
        )

    def get_leaderboard(
        self,
        school: str | None = None,
        department: str | None = None,
        role: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[TrustLeaderboardEntryResponse]:
        users = self.trust_repo.get_leaderboard(
            school=school,
            department=department,
            role=role,
            skip=skip,
            limit=limit,
        )
        entries = []
        for idx, u in enumerate(users):
            entries.append(
                TrustLeaderboardEntryResponse(
                    user_id=u.id,
                    name=u.name,
                    email=u.email,
                    school=u.school,
                    department=u.department,
                    trust_score=u.trust_score,
                    trust_badge=self.get_trust_badge(u.trust_score),
                    is_verified=u.verification_status
                    in ("verified", "approved"),
                    rank=skip + idx + 1,
                )
            )
        return entries

    def get_campus_analytics(self) -> TrustAnalyticsResponse:
        raw = self.trust_repo.get_campus_analytics()
        return TrustAnalyticsResponse.model_validate(raw)

    def get_trust_history(
        self, user_id: str, skip: int = 0, limit: int = 50
    ) -> list[TrustHistoryResponse]:
        rows = self.trust_repo.get_history_by_user_id(
            user_id, skip=skip, limit=limit
        )
        return [TrustHistoryResponse.model_validate(r) for r in rows]
