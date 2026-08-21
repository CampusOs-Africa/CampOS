from datetime import UTC, datetime

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Query,
    UploadFile,
)
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import CampusOSException
from app.core.rate_limit import otp_limiter
from app.core.security import get_current_user_strict, require_admin
from app.models.user import User
from app.schemas.verification import (
    AdminReviewRequest,
    CampusIdentityQRPayload,
    CampusIdentityQRScanRequest,
    CampusIdentityQRScanResponse,
    EmailOTPSendRequest,
    EmailOTPSendResponse,
    EmailOTPVerifyRequest,
    EmailOTPVerifyResponse,
    StudentVerificationResponse,
    VerificationHistoryResponse,
    VerificationStatusResponse,
)
from app.services.blockchain_service import quai_blockchain_service
from app.services.qr_service import qr_identity_service
from app.services.verification_service import VerificationService

router = APIRouter(prefix="/verification", tags=["Verified Student Identity"])


def utc_now_iso():
    return datetime.now(UTC).isoformat()


def get_verification_service(
    db: Session = Depends(get_db),
) -> VerificationService:
    return VerificationService(db=db)


@router.post(
    "/send-email-otp",
    response_model=EmailOTPSendResponse,
    summary="Send institutional email verification OTP",
    description="Dispatches a 6-digit OTP to the student's university email address (.edu.ng) via Resend.",
)
async def send_email_otp(
    body: EmailOTPSendRequest,
    service: VerificationService = Depends(get_verification_service),
    current_user: User = Depends(get_current_user_strict),
    _r=Depends(otp_limiter),
):
    return await service.send_email_otp(
        user_id=current_user.id, email=body.email
    )


@router.post(
    "/verify-email-otp",
    response_model=EmailOTPVerifyResponse,
    summary="Verify institutional email OTP code",
)
async def verify_email_otp(
    body: EmailOTPVerifyRequest,
    service: VerificationService = Depends(get_verification_service),
    current_user: User = Depends(get_current_user_strict),
    _r=Depends(otp_limiter),
):
    return await service.verify_email_otp(
        user_id=current_user.id, email=body.email, otp_code=body.otp_code
    )


@router.post(
    "/upload",
    response_model=StudentVerificationResponse,
    status_code=201,
    summary="Upload student ID and admission letter for verification",
    description="Submits institutional email (.edu.ng) and Cloudinary-hosted verification documents.",
)
async def upload_verification(
    student_id: UploadFile = File(
        ..., description="Student ID document (PDF, PNG, JPG <= 5MB)"
    ),
    admission_letter: UploadFile = File(
        ..., description="Admission letter document (PDF, PNG, JPG <= 5MB)"
    ),
    university_email: str | None = Form(
        None,
        description="University email (.edu.ng/.edu). Defaults to the profile school email.",
    ),
    service: VerificationService = Depends(get_verification_service),
    current_user: User = Depends(get_current_user_strict),
):
    # A user may only submit verification for themselves. The school email
    # defaults to the one saved on their profile when not explicitly provided.
    email = university_email or current_user.school_email
    if not email:
        raise CampusOSException(
            "A school/institutional email is required to submit verification. "
            "Add it to your profile or include it with this request.",
            status_code=400,
        )
    return await service.submit_verification(
        user_id=current_user.id,
        university_email=email,
        student_id_file=student_id,
        admission_letter_file=admission_letter,
    )


@router.get(
    "/status/{user_id}",
    response_model=VerificationStatusResponse,
    summary="Get user verification status",
    description="Returns current verification state, trust score, SHA-256 credential hash, tx_hash, and latest submission.",
)
def get_verification_status(
    user_id: str,
    service: VerificationService = Depends(get_verification_service),
    current_user: User = Depends(get_current_user_strict),
):
    if current_user.id != user_id and current_user.role != "admin":
        raise CampusOSException(
            "You can only view your own verification status.",
            status_code=403,
        )
    return service.get_verification_status(user_id=user_id)


@router.get(
    "/history/{user_id}",
    response_model=list[VerificationHistoryResponse],
    summary="Get verification audit history for user",
)
def get_verification_history(
    user_id: str,
    service: VerificationService = Depends(get_verification_service),
    current_user: User = Depends(get_current_user_strict),
):
    if current_user.id != user_id and current_user.role != "admin":
        raise CampusOSException(
            "You can only view your own verification history.",
            status_code=403,
        )
    return service.get_verification_history(user_id=user_id)


@router.post(
    "/admin/{verification_id}/approve",
    response_model=StudentVerificationResponse,
    summary="Admin approve verification request",
    description="Approves verification, generates SHA-256 hash, registers on Quai smart contract asynchronously, and awards +10 Trust Score.",
)
async def admin_approve_verification(
    verification_id: str,
    service: VerificationService = Depends(get_verification_service),
    admin: User = Depends(require_admin),
):
    return await service.admin_approve_verification(
        admin_id=admin.id, verification_id=verification_id
    )


@router.post(
    "/admin/{verification_id}/reject",
    response_model=StudentVerificationResponse,
    summary="Admin reject verification request",
    description="Rejects verification request with a mandatory explanation reason.",
)
async def admin_reject_verification(
    verification_id: str,
    body: AdminReviewRequest,
    service: VerificationService = Depends(get_verification_service),
    admin: User = Depends(require_admin),
):
    return await service.admin_reject_verification(
        admin_id=admin.id,
        verification_id=verification_id,
        reason=body.reason,
    )


@router.post(
    "/admin/{verification_id}/resubmit",
    response_model=StudentVerificationResponse,
    summary="Admin request verification resubmission",
    description="Requests student to re-upload documents with specific corrective instructions.",
)
async def admin_request_resubmission(
    verification_id: str,
    body: AdminReviewRequest,
    service: VerificationService = Depends(get_verification_service),
    admin: User = Depends(require_admin),
):
    return await service.admin_request_resubmission(
        admin_id=admin.id,
        verification_id=verification_id,
        reason=body.reason,
    )


@router.get(
    "/admin/queue",
    response_model=list[StudentVerificationResponse],
    summary="Admin verification queue",
    description="Returns filterable list of student verification requests for administrative review.",
)
def get_admin_queue(
    status: str
    | None = Query(
        None, description="Filter by status ('pending', 'approved', 'rejected', etc.)"
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    service: VerificationService = Depends(get_verification_service),
    admin: User = Depends(require_admin),
):
    return service.get_admin_queue(status=status, skip=skip, limit=limit)


@router.post(
    "/admin/revoke",
    summary="Admin revoke a previously verified student",
    description=(
        "Revokes verification, immediately removing the user's ability to sell "
        "and suspending their active listings. Existing listings are retained "
        "for audit but removed from the active catalog."
    ),
)
async def admin_revoke_verification(
    body: AdminReviewRequest,
    user_id: str = Query(..., description="UUID of the student to revoke"),
    service: VerificationService = Depends(get_verification_service),
    admin: User = Depends(require_admin),
):
    return await service.admin_revoke_verification(
        admin_id=admin.id, user_id=user_id, reason=body.reason
    )


@router.get(
    "/blockchain/{user_id}",
    summary="Verify on-chain credential proof on Quai Network",
    description="Returns simulated or live on-chain verification state, SHA-256 hash, and transaction receipt from Quai StudentIdentity contract.",
)
async def verify_blockchain_credential(
    user_id: str,
    service: VerificationService = Depends(get_verification_service),
):
    user = service.user_repo.get_by_id(user_id)
    if not user:
        raise CampusOSException(
            "User not found.",
            status_code=404,
        )
    blockchain_identity = user.wallet_address
    if not blockchain_identity and settings.USE_MOCK_BLOCKCHAIN:
        blockchain_identity = user.id
    if not blockchain_identity:
        raise CampusOSException(
            "User has not connected a wallet yet.",
            status_code=404,
        )
    return await quai_blockchain_service.verifyCredential(blockchain_identity)


@router.get(
    "/qr/{user_id}",
    response_model=CampusIdentityQRPayload,
    summary="Generate signed permanent Campus Identity QR payload",
    description="Generates an HMAC-SHA256 cryptographically signed QR token encoding student UUID, status, blockchain credential ID, and timestamp.",
)
def get_campus_identity_qr(
    user_id: str,
    service: VerificationService = Depends(get_verification_service),
):
    status_data = service.get_verification_status(user_id=user_id)
    if status_data["verification_status"] not in ("verified", "approved"):
        raise CampusOSException(
            "User must possess an approved Verified Student Identity to generate a permanent Campus Identity QR.",
            status_code=400,
        )

    cred_id = (
        status_data.get("credential_hash")
        or status_data.get("tx_hash")
        or "quai-on-chain-credential"
    )
    timestamp_str = (
        status_data["approved_at"].isoformat()
        if status_data.get("approved_at")
        else utc_now_iso()
    )

    return qr_identity_service.generate_campus_identity_qr(
        user_id=user_id,
        status=status_data["verification_status"],
        credential_id=cred_id,
        timestamp=timestamp_str,
    )


@router.post(
    "/qr/scan",
    response_model=CampusIdentityQRScanResponse,
    summary="Scan and verify a Campus Identity QR payload",
    description="Cryptographically validates an HMAC-SHA256 Campus Identity QR payload for administrators, merchants, and campus access control.",
)
async def scan_campus_identity_qr(
    body: CampusIdentityQRScanRequest,
    service: VerificationService = Depends(get_verification_service),
):
    verified_payload = qr_identity_service.verify_campus_identity_qr(body.payload)

    user_id = str(verified_payload["user_id"])
    status_data = service.get_verification_status(user_id=user_id)
    current_db_status = status_data["verification_status"]
    if current_db_status not in ("verified", "approved"):
        raise CampusOSException(
            f"User verification status is currently '{current_db_status}'. Credential is no longer active.",
            status_code=403,
        )

    user = service.user_repo.get_by_id(user_id)
    if not user:
        raise CampusOSException(
            "User not found.",
            status_code=404,
        )
    blockchain_identity = user.wallet_address
    if not blockchain_identity and settings.USE_MOCK_BLOCKCHAIN:
        blockchain_identity = user.id
    if not blockchain_identity:
        raise CampusOSException(
            "User has not connected a wallet yet.",
            status_code=404,
        )

    is_on_chain_verif = await quai_blockchain_service.isVerified(blockchain_identity)

    return {
        "valid": True,
        "user_id": user_id,
        "status": str(verified_payload["status"]),
        "credential_id": str(verified_payload["credential_id"]),
        "timestamp": str(verified_payload["timestamp"]),
        "signature": str(verified_payload["signature"]),
        "on_chain_status": "verified" if is_on_chain_verif else "unverified",
        "verified_by": "CampusOS Cryptographic Signature & Quai Network Engine",
    }
