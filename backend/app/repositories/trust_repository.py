from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.trust import TrustHistory
from app.models.user import User


def utc_now():
    return datetime.now(UTC)


class TrustRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_history(self, history: TrustHistory) -> TrustHistory:
        self.db.add(history)
        self.db.commit()
        self.db.refresh(history)
        return history

    def get_history_by_user_id(
        self, user_id: str, skip: int = 0, limit: int = 50
    ) -> list[TrustHistory]:
        return (
            self.db.query(TrustHistory)
            .filter(TrustHistory.user_id == user_id)
            .order_by(TrustHistory.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_recent_events_count(self, hours: int = 24) -> int:
        cutoff = utc_now() - timedelta(hours=hours)
        return (
            self.db.query(func.count(TrustHistory.id))
            .filter(TrustHistory.created_at >= cutoff)
            .scalar()
            or 0
        )

    def get_leaderboard(
        self,
        school: str | None = None,
        department: str | None = None,
        role: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[User]:
        query = self.db.query(User)
        if school and school.lower() != "all":
            query = query.filter(User.school == school)
        if department and department.lower() != "all":
            query = query.filter(User.department == department)
        if role and role.lower() != "all":
            query = query.filter(User.role == role)

        return (
            query.order_by(User.trust_score.desc(), User.name.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_campus_analytics(self) -> dict[str, Any]:
        avg_score = (
            self.db.query(func.avg(User.trust_score)).scalar() or 50.0
        )
        total_verif = (
            self.db.query(func.count(User.id))
            .filter(User.verification_status.in_(["verified", "approved"]))
            .scalar()
            or 0
        )

        all_users = self.db.query(User.trust_score).all()
        dist = {
            "Platinum (85-100)": 0,
            "Gold (70-84)": 0,
            "Silver (55-69)": 0,
            "Bronze (40-54)": 0,
            "At-Risk (0-39)": 0,
        }
        for (score,) in all_users:
            if score >= 85:
                dist["Platinum (85-100)"] += 1
            elif score >= 70:
                dist["Gold (70-84)"] += 1
            elif score >= 55:
                dist["Silver (55-69)"] += 1
            elif score >= 40:
                dist["Bronze (40-54)"] += 1
            else:
                dist["At-Risk (0-39)"] += 1

        recent_events = self.get_recent_events_count(hours=24)

        return {
            "campus_average_score": round(float(avg_score), 1),
            "total_verified_students": int(total_verif),
            "score_distribution": dist,
            "recent_trust_events_24h": int(recent_events),
        }
