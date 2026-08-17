import pytest

from app.core.exceptions import CampusOSException
from app.services.qr_service import qr_identity_service


def test_qr_identity_service_generation_and_verification():
    user_id = "user-test-uuid-001"
    status = "verified"
    cred_id = "0xquai_test_credential_hash_123"
    timestamp = "2026-07-30T10:00:00Z"

    # 1. Generate signed payload
    qr_payload = qr_identity_service.generate_campus_identity_qr(
        user_id=user_id,
        status=status,
        credential_id=cred_id,
        timestamp=timestamp,
    )
    assert qr_payload["user_id"] == user_id
    assert qr_payload["status"] == status
    assert qr_payload["credential_id"] == cred_id
    assert len(qr_payload["signature"]) == 64  # HMAC-SHA256 hex digest length
    assert "payload_string" in qr_payload

    # 2. Verify authentic payload
    verified = qr_identity_service.verify_campus_identity_qr(qr_payload)
    assert verified["valid"] is True
    assert verified["user_id"] == user_id
    assert verified["verified_by"] == "CampusOS HMAC-SHA256 Cryptographic Engine"

    # 3. Test tampered signature rejection
    tampered_payload = {
        **qr_payload,
        "signature": "0000000000000000000000000000000000000000000000000000000000000000"
    }
    with pytest.raises(CampusOSException) as exc_info:
        qr_identity_service.verify_campus_identity_qr(tampered_payload)
    assert exc_info.value.status_code == 400
    assert "Invalid Campus Identity QR cryptographic signature" in exc_info.value.message

    # 4. Test missing field rejection
    incomplete_payload = {
        "user_id": user_id,
        "status": status
    }
    with pytest.raises(CampusOSException) as exc_info:
        qr_identity_service.verify_campus_identity_qr(incomplete_payload)
    assert exc_info.value.status_code == 400
    assert "Malformed Campus Identity QR payload" in exc_info.value.message
