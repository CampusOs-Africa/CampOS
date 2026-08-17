import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.exceptions import CampusOSException, EntityNotFoundError, ForbiddenError
from app.models.fraud import FraudReport
from app.models.user import User
from app.repositories.fraud_repository import FraudRepository
from app.repositories.user_repository import UserRepository
from app.schemas.fraud import (
    FraudReportCreateRequest,
    FraudReportResolveRequest,
    FraudReportResponse,
)
from app.services.trust_service import TrustService

logger = logging.getLogger("campusos.fraud")


def utc_now():
    return datetime.now(UTC)


class FraudService:
    def __init__(self, db: Session):
        self.db = db
        self.fraud_repo = FraudRepository(db)
        self.user_repo = UserRepository(db)
        self.trust_service = TrustService(db)

    def _enrich_report(self, report: FraudReport) -> FraudReportResponse:
        return self._enrich_reports([report])[0]

    def _enrich_reports(
        self, reports: list[FraudReport]
    ) -> list[FraudReportResponse]:
        if not reports:
            return []
        user_ids = list(
            set(
                [r.reporter_id for r in reports]
                + [r.reported_user_id for r in reports]
            )
        )
        users = self.db.query(User).filter(User.id.in_(user_ids)).all()
        user_map = {u.id: u.name for u in users}

        res_list = []
        for r in reports:
            res = FraudReportResponse.model_validate(r)
            res.reporter_name = user_map.get(r.reporter_id)
            res.reported_user_name = user_map.get(r.reported_user_id)
            res_list.append(res)
        return res_list

    def submit_report(self, req: FraudReportCreateRequest) -> FraudReportResponse:
        reporter = self.user_repo.get_by_id(req.reporter_id)
        if not reporter:
            raise EntityNotFoundError("User", req.reporter_id)

        reported_user = self.user_repo.get_by_id(req.reported_user_id)
        if not reported_user:
            raise EntityNotFoundError("User", req.reported_user_id)

        if req.reporter_id == req.reported_user_id:
            raise CampusOSException(
                "You cannot submit a fraud report against yourself.",
                status_code=400,
            )

        report = FraudReport(
            reporter_id=req.reporter_id,
            reported_user_id=req.reported_user_id,
            category=req.category.lower(),
            description=req.description,
            evidence_url=req.evidence_url,
            order_id=req.order_id,
            status="pending",
            penalty_applied=0,
        )
        created = self.fraud_repo.create(report)
        logger.info(
            f"Fraud report {created.id} submitted by {req.reporter_id} against {req.reported_user_id} (category: {req.category})"
        )
        return self._enrich_report(created)

    def list_reports(
        self,
        status: str | None = None,
        reported_user_id: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[FraudReportResponse]:
        reports = self.fraud_repo.get_reports(
            status=status,
            reported_user_id=reported_user_id,
            skip=skip,
            limit=limit,
        )
        return self._enrich_reports(reports)

    def get_report_by_id(self, report_id: str) -> FraudReportResponse:
        report = self.fraud_repo.get_by_id(report_id)
        if not report:
            raise EntityNotFoundError("FraudReport", report_id)
        return self._enrich_report(report)

    def resolve_report(
        self, admin_id: str, report_id: str, req: FraudReportResolveRequest
    ) -> FraudReportResponse:
        admin = self.user_repo.get_by_id(admin_id)
        if not admin or admin.role != "admin":
            raise ForbiddenError("Only administrators can resolve fraud reports.")

        report = self.fraud_repo.get_by_id(report_id)
        if not report:
            raise EntityNotFoundError("FraudReport", report_id)

        report.status = req.status.lower()
        report.admin_id = admin_id
        report.resolution_notes = req.resolution_notes
        report.resolved_at = utc_now()

        if req.status.lower() == "resolved_confirmed":
            penalty = abs(req.penalty_points)
            report.penalty_applied = penalty
            # Apply trust score deduction via TrustScoreService
            self.trust_service.penalize_fraud_report(
                report.reported_user_id,
                reason=f"Confirmed fraud ({report.category}): {req.resolution_notes}",
                penalty=-penalty,
                report_id=report.id,
            )
            logger.warning(
                f"Fraud report {report.id} confirmed against {report.reported_user_id}; deducted -{penalty} Trust Score."
            )
        else:
            report.penalty_applied = 0
            logger.info(
                f"Fraud report {report.id} dismissed by admin {admin_id} ({req.resolution_notes})"
            )

        updated = self.fraud_repo.update(report)
        return self._enrich_report(updated)
