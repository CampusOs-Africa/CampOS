from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.fraud import FraudReport


class FraudRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, report: FraudReport) -> FraudReport:
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def get_by_id(self, report_id: str) -> FraudReport | None:
        return (
            self.db.query(FraudReport)
            .filter(FraudReport.id == report_id)
            .first()
        )

    def update(self, report: FraudReport) -> FraudReport:
        self.db.commit()
        self.db.refresh(report)
        return report

    def get_reports(
        self,
        status: str | None = None,
        reported_user_id: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[FraudReport]:
        query = self.db.query(FraudReport)
        if status and status.lower() != "all":
            query = query.filter(FraudReport.status == status.lower())
        if reported_user_id:
            query = query.filter(
                FraudReport.reported_user_id == reported_user_id
            )

        return (
            query.order_by(FraudReport.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count_confirmed_by_user(self, user_id: str) -> int:
        return (
            self.db.query(func.count(FraudReport.id))
            .filter(
                FraudReport.reported_user_id == user_id,
                FraudReport.status == "resolved_confirmed",
            )
            .scalar()
            or 0
        )
