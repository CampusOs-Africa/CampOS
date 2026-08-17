import hashlib
import hmac
import json
from typing import Any

from app.core.config import settings
from app.core.exceptions import CampusOSException


class QRIdentityService:
    """
    Cryptographic QR Service for Permanent Campus Identity.
    Generates and verifies HMAC-SHA256 digital signatures encoding:
    - Student UUID
    - Verification Status
    - Blockchain Credential ID (SHA-256 hash or Quai Tx Hash)
    - Verification Timestamp
    - Digital Signature (HMAC-SHA256 proof)
    """

    @staticmethod
    def _compute_signature(
        user_id: str,
        status: str,
        credential_id: str,
        timestamp: str,
    ) -> str:
        canonical_data = f"{user_id}|{status}|{credential_id}|{timestamp}"
        return hmac.new(
            settings.QR_SECRET_KEY.encode("utf-8"),
            canonical_data.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def generate_campus_identity_qr(
        self,
        user_id: str,
        status: str,
        credential_id: str,
        timestamp: str,
    ) -> dict[str, str]:
        """Generate signed Campus Identity QR payload."""
        signature = self._compute_signature(
            user_id=user_id,
            status=status,
            credential_id=credential_id,
            timestamp=timestamp,
        )
        payload_dict = {
            "user_id": user_id,
            "status": status,
            "credential_id": credential_id,
            "timestamp": timestamp,
            "signature": signature,
        }
        return {
            **payload_dict,
            "payload_string": json.dumps(payload_dict, sort_keys=True),
        }

    def verify_campus_identity_qr(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Verify HMAC-SHA256 cryptographic signature of a scanned Campus Identity QR."""
        required_keys = {"user_id", "status", "credential_id", "timestamp", "signature"}
        if not required_keys.issubset(payload.keys()):
            missing = required_keys - set(payload.keys())
            raise CampusOSException(
                f"Malformed Campus Identity QR payload. Missing fields: {missing}",
                status_code=400,
            )

        expected_sig = self._compute_signature(
            user_id=str(payload["user_id"]),
            status=str(payload["status"]),
            credential_id=str(payload["credential_id"]),
            timestamp=str(payload["timestamp"]),
        )

        if not hmac.compare_digest(expected_sig, str(payload["signature"])):
            raise CampusOSException(
                "Invalid Campus Identity QR cryptographic signature. Payload verification failed.",
                status_code=400,
            )

        return {
            "valid": True,
            "user_id": payload["user_id"],
            "status": payload["status"],
            "credential_id": payload["credential_id"],
            "timestamp": payload["timestamp"],
            "signature": payload["signature"],
            "verified_by": "CampusOS HMAC-SHA256 Cryptographic Engine",
        }


# Singleton instance for dependency injection across CampusOS backend
qr_identity_service = QRIdentityService()
