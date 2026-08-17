"""Admin operations: dashboard metrics, moderation, and audit logging."""

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.exceptions import CampusOSException, EntityNotFoundError, ForbiddenError
from app.models.admin_audit import AdminAuditLog
from app.models.escrow import EscrowRecord
from app.models.fraud import FraudReport
from app.models.marketplace import MarketplaceListing
from app.models.order import Order
from app.models.review import Review
from app.models.user import User
from app.models.verification import StudentVerification
from app.repositories.fraud_repository import FraudRepository
from app.repositories.marketplace_repository import MarketplaceRepository
from app.repositories.review_repository import ReviewRepository
from app.repositories.user_repository import UserRepository
from app.repositories.verification_repository import VerificationRepository

logger = logging.getLogger("campusos.admin")

VALID_ROLES = ("student", "admin", "verified_student", "moderator")


def utc_now() -> datetime:
    return datetime.now(UTC)


class AdminService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.verif = VerificationRepository(db)
        self.fraud = FraudRepository(db)
        self.reviews = ReviewRepository(db)
        self.listings = MarketplaceRepository(db)

    # ------------------------------------------------------------------ audit
    def _audit(
        self,
        admin_id: str,
        action: str,
        target_type: str | None = None,
        target_id: str | None = None,
        reason: str | None = None,
    ) -> None:
        try:
            log = AdminAuditLog(
                admin_id=admin_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                reason=reason,
            )
            self.db.add(log)
            self.db.commit()
        except Exception:  # audit must never break the operation
            self.db.rollback()
            logger.exception("Failed to write admin audit log")

    def get_audit_logs(self, limit: int = 100) -> list[dict]:
        rows = (
            self.db.query(AdminAuditLog)
            .order_by(AdminAuditLog.created_at.desc())
            .limit(limit)
            .all()
        )
        return [r.to_dict() for r in rows]

    # -------------------------------------------------------------- dashboard
    def dashboard(self) -> dict[str, Any]:
        def count(model, *criteria):
            q = self.db.query(func.count(model.id))
            if criteria:
                q = q.filter(*criteria)
            return int(q.scalar() or 0)

        total_users = count(User)
        verified = count(
            User, User.verification_status.in_(["verified", "approved"])
        )
        pending_verif = count(StudentVerification, StudentVerification.status == "pending")
        rejected_verif = count(
            StudentVerification, StudentVerification.status == "rejected"
        )
        revoked = count(User, User.verification_status == "revoked")

        active_listings = count(MarketplaceListing, MarketplaceListing.status == "active")
        suspended_listings = count(
            MarketplaceListing, MarketplaceListing.status == "suspended"
        )

        total_orders = count(Order)
        completed_orders = count(Order, Order.status == "completed")
        pending_orders = count(
            Order, Order.status.in_(["initiated", "escrow_locked", "escrow_funded"])
        )
        disputed_orders = count(Order, Order.status == "disputed")

        escrow_states = dict(
            self.db.query(EscrowRecord.state, func.count(EscrowRecord.id))
            .group_by(EscrowRecord.state)
            .all()
        )
        escrow_total = float(
            self.db.query(func.coalesce(func.sum(EscrowRecord.amount), 0.0)).scalar() or 0.0
        )
        order_total = float(
            self.db.query(func.coalesce(func.sum(Order.amount), 0.0)).scalar() or 0.0
        )

        pending_fraud = count(FraudReport, FraudReport.status == "pending")
        pending_reviews = count(Review, Review.status == "flagged")

        recent_verif = (
            self.db.query(StudentVerification)
            .order_by(StudentVerification.created_at.desc())
            .limit(5)
            .all()
        )
        recent_fraud = (
            self.db.query(FraudReport)
            .order_by(FraudReport.created_at.desc())
            .limit(5)
            .all()
        )
        recent_orders = (
            self.db.query(Order).order_by(Order.created_at.desc()).limit(5).all()
        )
        recent_listings = (
            self.db.query(MarketplaceListing)
            .order_by(MarketplaceListing.created_at.desc())
            .limit(5)
            .all()
        )

        return {
            "counts": {
                "users": total_users,
                "verified_students": verified,
                "pending_verifications": pending_verif,
                "rejected_verifications": rejected_verif,
                "revoked_students": revoked,
                "active_listings": active_listings,
                "suspended_listings": suspended_listings,
                "orders": total_orders,
                "pending_orders": pending_orders,
                "completed_orders": completed_orders,
                "disputed_orders": disputed_orders,
                "pending_fraud_reports": pending_fraud,
                "pending_review_moderation": pending_reviews,
            },
            "escrow": {"states": escrow_states, "total_amount": escrow_total},
            "payments": {"total_order_amount": order_total},
            "recent": {
                "verifications": [self._verification_summary(v) for v in recent_verif],
                "fraud_reports": [self._fraud_summary(r) for r in recent_fraud],
                "orders": [self._order_summary(o) for o in recent_orders],
                "listings": [self._listing_summary(l) for l in recent_listings],
            },
            "generated_at": utc_now().isoformat(),
        }

    # ----------------------------------------------------------------- users
    def list_users(
        self,
        status: str | None = None,
        role: str | None = None,
        q: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[dict]:
        query = self.db.query(User)
        if status:
            query = query.filter(User.verification_status == status)
        if role:
            query = query.filter(User.role == role)
        if q:
            like = f"%{q.lower()}%"
            query = query.filter(
                (func.lower(User.name).like(like))
                | (func.lower(User.email).like(like))
            )
        users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
        return [self._user_summary(u) for u in users]

    def get_user(self, user_id: str) -> dict:
        user = self.users.get_by_id(user_id)
        if not user:
            raise EntityNotFoundError("User", user_id)
        data = self._user_detail(user)
        data["verification"] = self.verif.get_by_user_id(user_id)
        return data

    def update_user_status(
        self, admin: User, user_id: str, is_active: bool
    ) -> dict:
        user = self.users.get_by_id(user_id)
        if not user:
            raise EntityNotFoundError("User", user_id)
        if not is_active and user.role == "admin":
            admin_count = self.db.query(func.count(User.id)).filter(
                User.role == "admin", User.is_active.is_(True)
            ).scalar()
            if admin_count <= 1:
                raise ForbiddenError("Cannot deactivate the last active admin.")
        user.is_active = is_active
        self.users.update(user)
        self._audit(
            admin.id,
            "user.status_change",
            "user",
            user_id,
            f"is_active={is_active}",
        )
        return self._user_detail(user)

    def update_user_role(self, admin: User, user_id: str, role: str) -> dict:
        if role not in VALID_ROLES:
            raise CampusOSException(
                f"Invalid role '{role}'. Allowed: {', '.join(VALID_ROLES)}",
                status_code=400,
            )
        user = self.users.get_by_id(user_id)
        if not user:
            raise EntityNotFoundError("User", user_id)
        # Protect against removing the last administrator.
        if user.role == "admin" and role != "admin":
            admin_count = self.db.query(func.count(User.id)).filter(
                User.role == "admin", User.is_active.is_(True)
            ).scalar()
            if admin_count <= 1:
                raise ForbiddenError("Cannot demote the last active admin.")
        user.role = role
        self.users.update(user)
        self._audit(admin.id, "user.role_change", "user", user_id, f"role={role}")
        return self._user_detail(user)

    # ------------------------------------------------------------ verifications
    def list_verifications(self, status: str | None = None) -> list[dict]:
        rows = self.verif.get_queue(status=status)
        return [self._verification_summary(v, include_documents=True) for v in rows]

    # ------------------------------------------------------------- listings
    def list_listings(
        self, status: str | None = None, skip: int = 0, limit: int = 50
    ) -> list[dict]:
        query = self.db.query(MarketplaceListing)
        if status:
            query = query.filter(MarketplaceListing.status == status)
        rows = query.order_by(MarketplaceListing.created_at.desc()).offset(skip).limit(limit).all()
        return [self._listing_summary(l) for l in rows]

    def moderate_listing(
        self,
        admin: User,
        listing_id: str,
        suspend: bool,
        reason: str | None = None,
    ) -> dict:
        listing = self.listings.get_by_id(listing_id)
        if not listing:
            raise EntityNotFoundError("MarketplaceListing", listing_id)
        seller = self.users.get_by_id(listing.seller_id)
        # Restoring must not bypass seller verification requirements.
        if not suspend:
            if not seller or seller.verification_status not in ("verified", "approved"):
                raise ForbiddenError(
                    "Cannot restore a listing whose seller is not verified."
                )
            listing.status = "active"
            action = "listing.restore"
        else:
            listing.status = "suspended"
            action = "listing.suspend"
        self.listings.update(listing)
        self._audit(admin.id, action, "listing", listing_id, reason)
        return self._listing_summary(listing)

    # ---------------------------------------------------------------- orders
    def list_orders(
        self, status: str | None = None, skip: int = 0, limit: int = 50
    ) -> list[dict]:
        query = self.db.query(Order)
        if status:
            query = query.filter(Order.status == status)
        rows = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
        return [self._order_summary(o) for o in rows]

    def get_order_detail(self, order_id: str) -> dict:
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise EntityNotFoundError("Order", order_id)
        summary = self._order_summary(order)
        escrow = self.db.query(EscrowRecord).filter(EscrowRecord.order_id == order_id).first()
        summary["escrow"] = (
            {
                "state": escrow.state,
                "amount": escrow.amount,
                "escrow_tx_hash": escrow.escrow_tx_hash,
            }
            if escrow
            else None
        )
        return summary

    # --------------------------------------------------------------- summaries
    def _user_summary(self, u: User) -> dict:
        return {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role,
            "verification_status": u.verification_status,
            "is_active": u.is_active,
            "trust_score": u.trust_score,
            "created_at": u.created_at,
        }

    def _user_detail(self, u: User) -> dict:
        data = self._user_summary(u)
        data.update(
            {
                "phone": u.phone,
                "school": u.school,
                "faculty": u.faculty,
                "department": u.department,
                "level": u.level,
                "matric_number": u.matric_number,
                "school_email": u.school_email,
                "wallet_address": u.wallet_address,
            }
        )
        return data

    def _verification_summary(
        self, v: StudentVerification, include_documents: bool = False
    ) -> dict:
        data = {
            "id": v.id,
            "user_id": v.user_id,
            "university_email": v.university_email,
            "status": v.status,
            "approved_by": v.approved_by,
            "rejection_reason": v.rejection_reason,
            "credential_hash": v.credential_hash,
            "created_at": v.created_at,
            "approved_at": v.approved_at,
        }
        if include_documents:
            data["student_id_url"] = v.student_id_url
            data["admission_letter_url"] = v.admission_letter_url
        return data

    def _fraud_summary(self, r: FraudReport) -> dict:
        return {
            "id": r.id,
            "reporter_id": r.reporter_id,
            "reported_user_id": r.reported_user_id,
            "category": r.category,
            "status": r.status,
            "order_id": r.order_id,
            "penalty_applied": r.penalty_applied,
            "created_at": r.created_at,
        }

    def _order_summary(self, o: Order) -> dict:
        return {
            "id": o.id,
            "buyer_id": o.buyer_id,
            "seller_id": o.seller_id,
            "listing_id": o.listing_id,
            "amount": o.amount,
            "status": o.status,
            "payment_reference": o.payment_reference,
            "created_at": o.created_at,
        }

    def _listing_summary(self, l: MarketplaceListing) -> dict:
        return {
            "id": l.id,
            "seller_id": l.seller_id,
            "title": l.title,
            "category": l.category,
            "price": l.price,
            "status": l.status,
            "inventory_count": l.inventory_count,
            "created_at": l.created_at,
        }
