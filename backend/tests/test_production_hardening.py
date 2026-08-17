"""
Automated Integration & Security Test Suite for CampusOS Production Hardening
=============================================================================

Tests all 6 outstanding production engineering improvements:
1. Redis-backed distributed rate limiting & in-memory graceful fallback
2. Institutional Email OTP verification (/send-email-otp & /verify-email-otp) with cooldown & attempt limits
3. Secret management: environment validation & multi-key secret rotation
4. CORS lockdown: production allowlist vs development fallback
5. Webhook replay protection: timestamp drift validation (±300 seconds) & Redis/in-memory replay cache
6. Improved logging: structured JSON logs, Request IDs, Correlation IDs & Audit events
"""

import time

import jwt
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.logger import log_audit_event
from app.core.security import verify_access_token
from app.main import app
from app.services.payment_service import PaymentService
from app.services.verification_service import _otp_cooldown_cache

client = TestClient(app)


def test_cors_lockdown_environments(client):
    """Verify production CORS allowlist vs local development fallback."""
    original_env = settings.ENVIRONMENT
    try:
        # Production mode must exclude wildcard "*" and only allow trusted production origins
        settings.ENVIRONMENT = "production"
        prod_origins = settings.get_cors_origins()
        assert "https://campusos.vercel.app" in prod_origins
        assert "https://campusos.ng" in prod_origins
        assert "*" not in prod_origins

        # Development mode must include localhost fallback origins
        settings.ENVIRONMENT = "development"
        dev_origins = settings.get_cors_origins()
        assert "http://localhost:3000" in dev_origins
        assert "http://127.0.0.1:3000" in dev_origins
    finally:
        settings.ENVIRONMENT = original_env


def test_secret_management_validation_and_rotation(client):
    """Verify production environment secret validation and multi-key rotation support."""
    original_env = settings.ENVIRONMENT
    try:
        # In test mode, validate_production_secrets returns inspection dict without error
        settings.ENVIRONMENT = "test"
        res_test = settings.validate_production_secrets()
        assert isinstance(res_test, dict)

        # In production mode, using default insecure keys must raise ValueError
        settings.ENVIRONMENT = "production"
        with pytest.raises(ValueError, match="CRITICAL: Insecure default secrets"):
            settings.validate_production_secrets()
    finally:
        settings.ENVIRONMENT = original_env

    # Test multi-key JWT secret rotation
    secondary_key = "campusos-rotated-secondary-jwt-secret-key-2026"
    settings.JWT_SECRET_KEY_ROTATION = secondary_key

    # Create a token signed with the secondary rotated key
    payload = {
        "sub": "user-rotated-e2e",
        "role": "student",
        "iat": int(time.time()),
        "exp": int(time.time() + 3600),
        "iss": "CampusOS-Auth-Engine",
    }
    rotated_token = jwt.encode(payload, secondary_key, algorithm=settings.JWT_ALGORITHM)

    # Verify our verify_access_token function successfully validates via secondary key in rotation
    decoded = verify_access_token(rotated_token)
    assert decoded["sub"] == "user-rotated-e2e"

    # Reset rotation setting
    settings.JWT_SECRET_KEY_ROTATION = ""


def test_email_otp_verification_lifecycle_and_cooldown(client):
    """Verify /send-email-otp and /verify-email-otp with cooldown and retry limits."""
    reg = client.post(
        "/api/v1/auth/register",
        json={"name": "Buhari Sani", "email": "b.sani.otp@abu.edu.ng", "password": "CampusOS2026!"},
    )
    assert reg.status_code == 201
    user_id = reg.json()["user"]["id"]
    auth = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    send_payload = {"email": "b.sani.otp@abu.edu.ng"}
    send_res = client.post("/api/v1/verification/send-email-otp", json=send_payload, headers=auth)
    assert send_res.status_code == 200
    send_data = send_res.json()
    assert send_data["success"] is True
    assert send_data["email"] == "b.sani.otp@abu.edu.ng"
    assert send_data["expires_in_seconds"] == 600

    cooldown_res = client.post("/api/v1/verification/send-email-otp", json=send_payload, headers=auth)
    assert cooldown_res.status_code == 429
    assert "Please wait" in cooldown_res.json()["error"]["message"]

    verify_payload_bad = {"email": "b.sani.otp@abu.edu.ng", "otp_code": "000000"}
    bad_res = client.post("/api/v1/verification/verify-email-otp", json=verify_payload_bad, headers=auth)
    assert bad_res.status_code == 400
    assert "2 attempts remaining" in bad_res.json()["error"]["message"]

    verify_payload_good = {"email": "b.sani.otp@abu.edu.ng", "otp_code": "123456"}
    good_res = client.post("/api/v1/verification/verify-email-otp", json=verify_payload_good, headers=auth)
    assert good_res.status_code == 200
    good_data = good_res.json()
    assert good_data["success"] is True
    assert good_data["user_id"] == user_id
    assert good_data["email"] == "b.sani.otp@abu.edu.ng"
    assert good_data["verified_at"] is not None

    _otp_cooldown_cache.pop("b.sani.otp@abu.edu.ng", None)


def test_webhook_replay_protection_and_timestamp_drift(client):
    """Verify Blip Pay webhook timestamp drift (±300 seconds) and replay cache TTL."""
    # 1. Test timestamp drift > 300 seconds rejection (401 Unauthorized)
    old_ts = str(int(time.time()) - 400)
    drift_res = client.post(
        "/api/v1/payments/webhook",
        headers={
            "X-Blip-Signature": "mock_sig_valid",
            "X-Blip-Timestamp": old_ts,
        },
        json={
            "payment_reference": "blip_pay_drift_test_1001",
            "status": "success",
            "amount": 5000.0,
        },
    )
    assert drift_res.status_code == 401
    assert "Invalid Blip Pay webhook" in drift_res.text

    # 2. Test replay cache helper directly
    ref = "blip_pay_replay_test_reference_2002"
    # First check should be False (not replayed)
    assert PaymentService.check_and_cache_webhook_replay(ref, ttl_seconds=3600) is False
    # Second check should be True (replayed!)
    assert PaymentService.check_and_cache_webhook_replay(ref, ttl_seconds=3600) is True


def test_improved_logging_request_and_correlation_ids(client):
    """Verify CorrelationIdMiddleware sets X-Request-ID and X-Correlation-ID headers and audit log helper."""
    # Call health check with custom X-Request-ID and X-Correlation-ID
    custom_req_id = "req-test-1111"
    custom_corr_id = "corr-test-2222"
    res = client.get(
        "/health",
        headers={
            "X-Request-ID": custom_req_id,
            "X-Correlation-ID": custom_corr_id,
        },
    )
    assert res.status_code == 200
    assert res.headers["x-request-id"] == custom_req_id
    assert res.headers["x-correlation-id"] == custom_corr_id

    # Verify structured audit event helper executes cleanly without error
    log_audit_event(
        action="TEST_PRODUCTION_AUDIT",
        actor_id="admin-user-001",
        target_id="target-resource-002",
        status="SUCCESS",
        details={"reason": "Security production hardening test"},
    )


def test_rate_limiting_middleware_sliding_window(client):
    """Verify RateLimitMiddleware enforces rate limit when X-Test-Rate-Limit header is passed."""
    # Send repeated requests to a sensitive endpoint with X-Test-Rate-Limit=true
    # Register a user to obtain a JWT (send-email-otp now requires auth).
    reg = client.post(
        "/api/v1/auth/register",
        json={"name": "Rate User", "email": "rate.test@unilag.edu.ng", "password": "CampusOS2026!"},
    )
    token = reg.json()["access_token"]
    test_ip_header = {
        "X-Test-Rate-Limit": "true",
        "X-Forwarded-For": "10.0.0.99",
        "Authorization": f"Bearer {token}",
    }

    # We send up to RATE_LIMIT_SENSITIVE_PER_MINUTE + 1 requests
    limit = settings.RATE_LIMIT_SENSITIVE_PER_MINUTE
    rate_limited = False

    for i in range(limit + 5):
        res = client.post(
            "/api/v1/verification/send-email-otp",
            headers=test_ip_header,
            json={"email": "rate.test@unilag.edu.ng"},
        )
        if res.status_code == 429 and "Too many requests" in res.text:
            rate_limited = True
            break

    assert rate_limited is True, "Rate limiter did not throttle requests when limit was exceeded."
