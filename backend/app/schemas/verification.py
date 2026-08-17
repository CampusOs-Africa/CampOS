from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EmailOTPSendRequest(BaseModel):
    # user_id is derived from the JWT; accepted only for backward compatibility
    # and ignored when an authenticated user is present.
    user_id: str | None = Field(None, description="UUID of the student user (derived from JWT)")
    email: str = Field(..., description="Institutional university email (.edu.ng)")


class EmailOTPSendResponse(BaseModel):
    success: bool
    message: str
    email: str
    expires_in_seconds: int = 600


class EmailOTPVerifyRequest(BaseModel):
    user_id: str | None = Field(None, description="UUID of the student user (derived from JWT)")
    email: str = Field(..., description="Institutional university email (.edu.ng)")
    otp_code: str = Field(
        ..., min_length=6, max_length=6, description="6-digit OTP code"
    )


class EmailOTPVerifyResponse(BaseModel):
    success: bool
    message: str
    user_id: str
    email: str
    verified_at: datetime


class VerificationHistoryResponse(BaseModel):
    id: str
    verification_id: str
    user_id: str
    old_status: str | None = None
    new_status: str
    changed_by: str | None = None
    reason: str | None = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class StudentVerificationResponse(BaseModel):
    id: str
    user_id: str
    student_id_url: str
    admission_letter_url: str
    university_email: str
    status: str
    approved_by: str | None = None
    rejection_reason: str | None = None
    credential_hash: str | None = None
    tx_hash: str | None = None
    created_at: datetime
    updated_at: datetime
    approved_at: datetime | None = None
    history: list[VerificationHistoryResponse] | None = None

    model_config = ConfigDict(from_attributes=True)


class AdminReviewRequest(BaseModel):
    reason: str = Field(..., min_length=3, description="Reason for rejection or resubmission request.")


class VerificationStatusResponse(BaseModel):
    user_id: str
    verification_status: str
    trust_score: int
    credential_hash: str | None = None
    tx_hash: str | None = None
    approved_at: datetime | None = None
    verification: StudentVerificationResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class BlockchainCredentialResponse(BaseModel):
    user_id: str
    credential_hash: str
    tx_hash: str
    status: str
    timestamp: str


class CampusIdentityQRPayload(BaseModel):
    user_id: str
    status: str
    credential_id: str
    timestamp: str
    signature: str
    payload_string: str


class CampusIdentityQRScanRequest(BaseModel):
    payload: dict[str, Any] = Field(..., description="Scanned JSON object from Campus Identity QR code")


class CampusIdentityQRScanResponse(BaseModel):
    valid: bool
    user_id: str
    status: str
    credential_id: str
    timestamp: str
    signature: str
    on_chain_status: str
    verified_by: str
