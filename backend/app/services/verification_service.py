import hmac
import logging
import time
import uuid
from datetime import UTC, datetime
from typing import Any

import httpx
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import (
    CampusOSException,
    DuplicateSubmissionError,
    EmailValidationError,
    EntityNotFoundError,
    ForbiddenError,
)
from app.models.user import User
from app.models.verification import StudentVerification, VerificationHistory
from app.repositories.user_repository import UserRepository
from app.repositories.verification_repository import VerificationRepository
from app.services.blockchain_service import (
    BlockchainService,
    quai_blockchain_service,
)
from app.services.storage_service import StorageService
from app.services.trust_score_service import TrustScoreService

logger = logging.getLogger("campusos.verification")
_otp_cache: dict[str, dict[str, Any]] = {}
_otp_cooldown_cache: dict[str, float] = {}


def utc_now():
    return datetime.now(UTC)


def validate_university_email(email: str) -> str:
    cleaned = email.lower().strip()
    if "@" not in cleaned:
        raise EmailValidationError("Invalid email address format.")

    domain = cleaned.split("@")[-1]
    # Check if institutional (.edu.ng, .edu, .ac.ng or academic domain)
    if not (
        domain.endswith((".edu.ng", ".edu", ".ac.ng"))
        or "univ" in domain
        or "school" in domain
        or "college" in domain
    ):
        raise EmailValidationError(
            f"Email '{cleaned}' does not belong to a recognized university academic domain (e.g., .edu.ng, .edu)."
        )
    return cleaned


class VerificationService:
    def __init__(
        self,
        db: Session,
        storage_service: StorageService | None = None,
        blockchain_service: BlockchainService | None = None,
    ):
        self.db = db
        self.user_repo = UserRepository(db)
        self.verif_repo = VerificationRepository(db)
        self.storage = storage_service or StorageService()
        self.blockchain = blockchain_service or quai_blockchain_service
        self.trust_service = TrustScoreService(db)

    def _check_admin_permission(self, admin_id: str) -> User:
        admin = self.user_repo.get_by_id(admin_id)
        if not admin or admin.role != "admin":
            raise ForbiddenError("Only administrators can perform verification review actions.")
        return admin

    async def submit_verification(
        self,
        user_id: str,
        university_email: str,
        student_id_file: UploadFile,
        admission_letter_file: UploadFile,
    ) -> StudentVerification:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise EntityNotFoundError("User", user_id)

        # 1. Check duplicate active submissions
        active = self.verif_repo.get_active_by_user_id(user_id)
        if active:
            raise DuplicateSubmissionError(
                f"User already has an active verification request (status: '{active.status}')."
            )

        # 2. Validate institutional email. An explicit value takes precedence;
        # otherwise use the school email saved on the user's profile.
        email_to_validate = university_email or user.school_email
        if not email_to_validate:
            raise CampusOSException(
                "A school/institutional email is required to submit verification. "
                "Add it to your profile or include it with this request.",
                status_code=400,
            )
        valid_email = validate_university_email(email_to_validate)
        email_owner = self.verif_repo.get_by_university_email(valid_email)
        if email_owner and email_owner.user_id != user_id:
            raise DuplicateSubmissionError(
                "This university email is already registered to another active student verification."
            )

        # Persist the school email on the profile for reuse.
        if (user.school_email or "").lower() != valid_email:
            user.school_email = valid_email

        # A previously verified user changing their school email must be
        # re-reviewed; the prior approval is no longer valid.
        if user.verification_status in ("verified", "approved"):
            user.verification_status = "pending"

        # 3. Upload files to Cloudinary (validates type & size)
        id_url = await self.storage.upload_file(student_id_file, folder="campusos/student_ids")
        letter_url = await self.storage.upload_file(
            admission_letter_file, folder="campusos/admission_letters"
        )

        # 4. Create StudentVerification record
        verif = StudentVerification(
            user_id=user_id,
            student_id_url=id_url,
            admission_letter_url=letter_url,
            university_email=valid_email,
            status="pending",
        )
        created = self.verif_repo.create(verif)

        # 5. Update user verification status
        user.verification_status = "pending"
        self.user_repo.update(user)

        # 6. Record VerificationHistory audit trail
        history = VerificationHistory(
            verification_id=created.id,
            user_id=user_id,
            old_status=None,
            new_status="pending",
            changed_by=user_id,
            reason="Submitted student identity documents for verification.",
        )
        self.verif_repo.create_history(history)

        return created

    def get_verification_status(self, user_id: str) -> dict:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise EntityNotFoundError("User", user_id)

        verif = self.verif_repo.get_by_user_id(user_id)
        return {
            "user_id": user_id,
            "verification_status": user.verification_status,
            "trust_score": user.trust_score,
            "credential_hash": verif.credential_hash if verif else None,
            "tx_hash": verif.tx_hash if verif else None,
            "approved_at": verif.approved_at if verif else None,
            "verification": verif,
        }

    async def send_email_otp(self, user_id: str, email: str) -> dict[str, Any]:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise EntityNotFoundError("User", user_id)

        valid_email = validate_university_email(email)

        now = time.time()
        cooldown_end = _otp_cooldown_cache.get(valid_email, 0)
        if now < cooldown_end:
            raise CampusOSException(
                f"Please wait {int(cooldown_end - now)} seconds before requesting another OTP.",
                status_code=429,
            )

        otp_code = (
            "123456"
            if (
                settings.USE_MOCK_EMAIL_OTP
                or settings.RESEND_API_KEY == "mock-resend-api-key"
            )
            else str(uuid.uuid4().int)[:6]
        )

        _otp_cache[f"{user_id}:{valid_email}"] = {
            "code": otp_code,
            "attempts": 0,
            "expires_at": now + settings.EMAIL_OTP_EXPIRE_SECONDS,
        }
        _otp_cooldown_cache[valid_email] = now + 60.0

        if (
            settings.USE_MOCK_EMAIL_OTP
            or settings.RESEND_API_KEY == "mock-resend-api-key"
        ):
            logger.info(
                f"[MOCK-RESEND] Sent email OTP '{otp_code}' to {valid_email} for user {user_id}"
            )
        else:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {settings.RESEND_API_KEY}"
                    },
                    json={
                        "from": "CampusOS <noreply@campusos.ng>",
                        "to": [valid_email],
                        "subject": "CampusOS — Institutional Email Verification OTP",
                        "text": f"Your CampusOS verification code is: {otp_code}. Valid for 10 minutes.",
                    },
                )
                res.raise_for_status()

        logger.info(
            f"Email OTP dispatched to {valid_email} for user {user_id} (Expires in {settings.EMAIL_OTP_EXPIRE_SECONDS}s)"
        )
        return {
            "success": True,
            "message": f"OTP sent to {valid_email}",
            "email": valid_email,
            "expires_in_seconds": settings.EMAIL_OTP_EXPIRE_SECONDS,
        }

    async def verify_email_otp(
        self, user_id: str, email: str, otp_code: str
    ) -> dict[str, Any]:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise EntityNotFoundError("User", user_id)

        valid_email = validate_university_email(email)
        cache_key = f"{user_id}:{valid_email}"
        stored = _otp_cache.get(cache_key)

        now = time.time()
        if not stored or now > stored["expires_at"]:
            _otp_cache.pop(cache_key, None)
            raise CampusOSException(
                "Email verification OTP has expired or was not found. Please request a new OTP.",
                status_code=400,
            )

        if stored["attempts"] >= settings.EMAIL_OTP_MAX_ATTEMPTS:
            _otp_cache.pop(cache_key, None)
            raise CampusOSException(
                "Maximum OTP verification attempts exceeded. Please request a new OTP.",
                status_code=403,
            )

        is_valid = hmac.compare_digest(stored["code"], otp_code) or (
            settings.USE_MOCK_EMAIL_OTP and otp_code == "123456"
        )

        if not is_valid:
            stored["attempts"] += 1
            remaining = settings.EMAIL_OTP_MAX_ATTEMPTS - stored["attempts"]
            raise CampusOSException(
                f"Invalid OTP code. {remaining} attempts remaining.",
                status_code=400,
            )

        _otp_cache.pop(cache_key, None)
        logger.info(
            f"Institutional email '{valid_email}' successfully verified for user {user_id}"
        )

        # Persist the verified school email on the user's profile.
        if (user.school_email or "").lower() != valid_email:
            user.school_email = valid_email

        verif = self.verif_repo.get_by_user_id(user_id)
        if verif:
            # Record the verified email against the verification record.
            if verif.university_email != valid_email:
                verif.university_email = valid_email
            history = VerificationHistory(
                verification_id=verif.id,
                user_id=user_id,
                old_status=verif.status,
                new_status=verif.status,
                changed_by=user_id,
                reason=f"Institutional email '{valid_email}' verified via OTP challenge.",
            )
            self.verif_repo.create_history(history)

        self.user_repo.update(user)

        return {
            "success": True,
            "message": "Institutional email verified successfully.",
            "user_id": user_id,
            "email": valid_email,
            "verified_at": utc_now(),
        }

    async def admin_approve_verification(
        self, admin_id: str, verification_id: str
    ) -> StudentVerification:
        self._check_admin_permission(admin_id)
        verif = self.verif_repo.get_by_id(verification_id)
        if not verif:
            raise EntityNotFoundError("StudentVerification", verification_id)

        old_status = verif.status
        if old_status == "approved":
            return verif

        user = self.user_repo.get_by_id(verif.user_id)
        if not user:
            raise EntityNotFoundError("User", verif.user_id)

        # Phase 1: Require that the user has a connected wallet before on-chain registration
        if not user.wallet_address:
            raise CampusOSException(
                "User must have a connected Quai wallet (User.wallet_address) before verification can be registered on-chain. "
                "Please ask the student to connect their wallet first.",
                status_code=400,
            )

        # 1. Generate SHA-256 cryptographic credential hash
        cred_hash = self.blockchain.createCredentialHash(
            user_id=verif.user_id,
            email=verif.university_email,
            student_id_url=verif.student_id_url,
            admission_letter_url=verif.admission_letter_url,
        )

        # 2. Store on Quai smart contract using real wallet address (Phase 1: canonical blockchain identity)
        tx_receipt = await self.blockchain.registerStudent(wallet_address=user.wallet_address, cred_hash=cred_hash)

        # 3. Update verification record
        verif.status = "approved"
        verif.approved_by = admin_id
        verif.credential_hash = cred_hash
        verif.tx_hash = tx_receipt.get("tx_hash")
        verif.approved_at = utc_now()
        verif.rejection_reason = None
        self.verif_repo.update(verif)

        # 4. Update user profile status & award +10 Trust Score via TrustScoreService
        user.verification_status = "verified"
        self.user_repo.update(user)
        self.trust_service.award_verification_bonus(
            verif.user_id, verification_id=verif.id
        )

        # 5. Record VerificationHistory
        history = VerificationHistory(
            verification_id=verif.id,
            user_id=verif.user_id,
            old_status=old_status,
            new_status="approved",
            changed_by=admin_id,
            reason=f"Approved by Administrator. Awarded +10 Trust Score and registered credential hash on Quai Network (tx_hash: {verif.tx_hash}).",
        )
        self.verif_repo.create_history(history)

        return verif

    async def admin_reject_verification(
        self, admin_id: str, verification_id: str, reason: str
    ) -> StudentVerification:
        self._check_admin_permission(admin_id)
        verif = self.verif_repo.get_by_id(verification_id)
        if not verif:
            raise EntityNotFoundError("StudentVerification", verification_id)

        old_status = verif.status
        user = self.user_repo.get_by_id(verif.user_id)
        if not user:
            raise EntityNotFoundError("User", verif.user_id)

        verif.status = "rejected"
        verif.approved_by = admin_id
        verif.rejection_reason = reason
        self.verif_repo.update(verif)

        user.verification_status = "rejected"
        self.user_repo.update(user)

        history = VerificationHistory(
            verification_id=verif.id,
            user_id=verif.user_id,
            old_status=old_status,
            new_status="rejected",
            changed_by=admin_id,
            reason=f"Rejected by Administrator: {reason}",
        )
        self.verif_repo.create_history(history)

        return verif

    async def admin_request_resubmission(
        self, admin_id: str, verification_id: str, reason: str
    ) -> StudentVerification:
        self._check_admin_permission(admin_id)
        verif = self.verif_repo.get_by_id(verification_id)
        if not verif:
            raise EntityNotFoundError("StudentVerification", verification_id)

        old_status = verif.status
        user = self.user_repo.get_by_id(verif.user_id)
        if not user:
            raise EntityNotFoundError("User", verif.user_id)

        verif.status = "resubmission_requested"
        verif.approved_by = admin_id
        verif.rejection_reason = reason
        self.verif_repo.update(verif)

        user.verification_status = "resubmission_requested"
        self.user_repo.update(user)

        history = VerificationHistory(
            verification_id=verif.id,
            user_id=verif.user_id,
            old_status=old_status,
            new_status="resubmission_requested",
            changed_by=admin_id,
            reason=f"Resubmission requested by Administrator: {reason}",
        )
        self.verif_repo.create_history(history)

        return verif

    async def admin_revoke_verification(
        self, admin_id: str, user_id: str, reason: str
    ) -> StudentVerification:
        """Revoke a previously verified student.

        The user immediately loses selling authorization. Existing listings are
        retained for audit but are suspended from the active catalog by status.
        """
        self._check_admin_permission(admin_id)
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise EntityNotFoundError("User", user_id)

        old_status = user.verification_status
        user.verification_status = "revoked"
        self.user_repo.update(user)

        # Suspend any active listings for the revoked seller.
        from app.models.marketplace import MarketplaceListing

        listings = (
            self.db.query(MarketplaceListing)
            .filter(
                MarketplaceListing.seller_id == user_id,
                MarketplaceListing.status.in_(["active", "pending_order"]),
            )
            .all()
        )
        for listing in listings:
            listing.status = "suspended"
        self.db.commit()

        verif = self.verif_repo.get_by_user_id(user_id)
        if verif:
            history = VerificationHistory(
                verification_id=verif.id,
                user_id=user_id,
                old_status=old_status,
                new_status="revoked",
                changed_by=admin_id,
                reason=f"Verification revoked by Administrator: {reason}",
            )
            self.verif_repo.create_history(history)

        return verif

    def get_verification_history(self, user_id: str) -> list[VerificationHistory]:
        return self.verif_repo.get_history_by_user_id(user_id)

    def get_admin_queue(
        self, status: str | None = None, skip: int = 0, limit: int = 100
    ) -> list[StudentVerification]:
        return self.verif_repo.get_queue(status=status, skip=skip, limit=limit)
