from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_admin
from app.models.fraud import FraudReport
from app.models.user import User
from app.schemas.admin import ListingModeration, RoleUpdate, StatusUpdate
from app.services.admin_service import AdminService
from app.services.fraud_service import FraudService
from app.services.review_service import ReviewService
from app.services.verification_service import VerificationService

router = APIRouter(prefix="/admin", tags=["Admin Operations"])


def service(db: Session = Depends(get_db)) -> AdminService:
    return AdminService(db)


# --------------------------------------------------------------- dashboard
@router.get("/dashboard", summary="Admin operational dashboard")
def dashboard(svc: AdminService = Depends(service), admin: User = Depends(require_admin)):
    return svc.dashboard()


@router.get("/audit", summary="Recent admin audit log")
def audit_log(
    limit: int = Query(100, ge=1, le=500),
    svc: AdminService = Depends(service),
    admin: User = Depends(require_admin),
):
    return svc.get_audit_logs(limit=limit)


# ------------------------------------------------------------------- users
@router.get("/users", summary="List users (admin only)")
def list_users(
    status: str | None = None,
    role: str | None = None,
    q: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    svc: AdminService = Depends(service),
    admin: User = Depends(require_admin),
):
    return svc.list_users(status=status, role=role, q=q, skip=skip, limit=limit)


@router.get("/users/{user_id}", summary="User detail (admin only)")
def get_user(
    user_id: str,
    svc: AdminService = Depends(service),
    admin: User = Depends(require_admin),
):
    return svc.get_user(user_id)


@router.patch("/users/{user_id}/status", summary="Activate/deactivate a user")
def update_user_status(
    user_id: str,
    body: StatusUpdate,
    svc: AdminService = Depends(service),
    admin: User = Depends(require_admin),
):
    return svc.update_user_status(admin, user_id, body.is_active)


@router.patch("/users/{user_id}/role", summary="Change a user's role")
def update_user_role(
    user_id: str,
    body: RoleUpdate,
    svc: AdminService = Depends(service),
    admin: User = Depends(require_admin),
):
    return svc.update_user_role(admin, user_id, body.role)


# ----------------------------------------------------------- verifications
@router.get("/verifications", summary="Verification queue")
def list_verifications(
    status: str | None = None,
    svc: AdminService = Depends(service),
    admin: User = Depends(require_admin),
):
    return svc.list_verifications(status=status)


@router.post("/verifications/{verification_id}/approve")
async def approve_verification(
    verification_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return await _verification_service(db).admin_approve_verification(admin.id, verification_id)


@router.post("/verifications/{verification_id}/reject")
async def reject_verification(
    verification_id: str,
    payload: dict,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    reason = (payload or {}).get("reason") or "Rejected by administrator."
    return await _verification_service(db).admin_reject_verification(
        admin.id, verification_id, reason
    )


@router.post("/verifications/{verification_id}/resubmit")
async def resubmit_verification(
    verification_id: str,
    payload: dict,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    reason = (payload or {}).get("reason") or "Please re-upload documents."
    return await _verification_service(db).admin_request_resubmission(
        admin.id, verification_id, reason
    )


@router.post("/verifications/revoke", summary="Revoke a verified student")
async def revoke_verification(
    payload: dict,
    user_id: str = Query(...),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    reason = (payload or {}).get("reason") or "Verification revoked."
    return await _verification_service(db).admin_revoke_verification(
        admin.id, user_id, reason
    )


@router.get("/verifications/{verification_id}/history")
def verification_history(
    verification_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    from app.repositories.verification_repository import VerificationRepository

    return VerificationRepository(db).get_history_by_verification_id(verification_id)


def _verification_service(db: Session) -> VerificationService:
    return VerificationService(db)


# ------------------------------------------------------------------- fraud
@router.get("/fraud", summary="Fraud report queue")
def list_fraud(
    status: str | None = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return FraudService(db).list_reports(status=status)


@router.get("/fraud/{report_id}")
def get_fraud(
    report_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    report = db.query(FraudReport).filter(FraudReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Fraud report not found.")
    return report


@router.post("/fraud/{report_id}/resolve")
def resolve_fraud(
    report_id: str,
    payload: dict,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    from app.schemas.fraud import FraudReportResolveRequest

    req = FraudReportResolveRequest(**(payload or {}))
    return FraudService(db).resolve_report(
        admin_id=admin.id, report_id=report_id, req=req
    )


# ------------------------------------------------------------------ reviews
@router.get("/reviews", summary="Review moderation queue")
def list_reviews(
    status: str = Query("flagged"),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return ReviewService(db).get_moderation_queue(status=status)


@router.post("/reviews/{review_id}/moderate")
def moderate_review(
    review_id: str,
    payload: dict,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    from app.schemas.review import ReviewModerateRequest

    req = ReviewModerateRequest(**(payload or {}))
    return ReviewService(db).moderate_review(
        admin_id=admin.id, review_id=review_id, status=req.status, reason=req.reason
    )


# ---------------------------------------------------------------- listings
@router.get("/listings", summary="All listings (admin)")
def list_listings(
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    svc: AdminService = Depends(service),
    admin: User = Depends(require_admin),
):
    return svc.list_listings(status=status, skip=skip, limit=limit)


@router.post("/listings/{listing_id}/suspend")
def suspend_listing(
    listing_id: str,
    body: ListingModeration,
    svc: AdminService = Depends(service),
    admin: User = Depends(require_admin),
):
    return svc.moderate_listing(admin, listing_id, suspend=True, reason=body.reason)


@router.post("/listings/{listing_id}/restore")
def restore_listing(
    listing_id: str,
    body: ListingModeration,
    svc: AdminService = Depends(service),
    admin: User = Depends(require_admin),
):
    return svc.moderate_listing(admin, listing_id, suspend=False, reason=body.reason)


# ------------------------------------------------------------------- orders
@router.get("/orders", summary="All orders (admin)")
def list_orders(
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    svc: AdminService = Depends(service),
    admin: User = Depends(require_admin),
):
    return svc.list_orders(status=status, skip=skip, limit=limit)


@router.get("/orders/{order_id}", summary="Order detail (admin)")
def get_order(
    order_id: str,
    svc: AdminService = Depends(service),
    admin: User = Depends(require_admin),
):
    return svc.get_order_detail(order_id)
