from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user_strict, require_admin
from app.models.user import User
from app.schemas.fraud import (
    FraudReportCreateRequest,
    FraudReportResolveRequest,
    FraudReportResponse,
)
from app.services.fraud_service import FraudService

router = APIRouter(prefix="/fraud", tags=["Fraud Reporting & Dispute Governance"])


def get_fraud_service(db: Session = Depends(get_db)) -> FraudService:
    return FraudService(db=db)


@router.post(
    "/reports",
    response_model=FraudReportResponse,
    status_code=201,
    summary="Submit a fraud or scam report",
)
def submit_fraud_report(
    body: FraudReportCreateRequest,
    service: FraudService = Depends(get_fraud_service),
    current_user: User = Depends(get_current_user_strict),
):
    # Reporter is always derived from the JWT.
    body.reporter_id = current_user.id
    return service.submit_report(body)


@router.get(
    "/reports",
    response_model=list[FraudReportResponse],
    summary="List fraud reports (admin only)",
)
def list_fraud_reports(
    status: str | None = Query(None),
    reported_user_id: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: FraudService = Depends(get_fraud_service),
    admin: User = Depends(require_admin),
):
    return service.list_reports(
        status=status,
        reported_user_id=reported_user_id,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/reports/{report_id}",
    response_model=FraudReportResponse,
    summary="Get fraud report details (admin only)",
)
def get_fraud_report_by_id(
    report_id: str,
    service: FraudService = Depends(get_fraud_service),
    admin: User = Depends(require_admin),
):
    return service.get_report_by_id(report_id)


@router.post(
    "/reports/{report_id}/resolve",
    response_model=FraudReportResponse,
    summary="Admin resolve fraud report",
)
def resolve_fraud_report(
    report_id: str,
    body: FraudReportResolveRequest,
    service: FraudService = Depends(get_fraud_service),
    admin: User = Depends(require_admin),
):
    return service.resolve_report(
        admin_id=admin.id, report_id=report_id, req=body
    )
