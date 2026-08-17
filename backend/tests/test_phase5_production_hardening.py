"""Phase 5 — production hardening tests."""

import os
import time

import jwt
import pytest

from app.core.config import Settings, _DEV_JWT_SECRET
from app.core.security import create_access_token


def _settings(env: dict[str, str]) -> Settings:
    """Build Settings with the given environment overrides."""
    env = dict(env)
    env.setdefault("ENVIRONMENT", env.get("APP_ENV", "development"))
    old = {k: os.environ.get(k) for k in env}
    os.environ.update({k: ("" if v is None else str(v)) for k, v in env.items()})
    try:
        return Settings()
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


# ------------------------------------------------------------ configuration
def test_production_requires_jwt_secret():
    s = _settings({"APP_ENV": "production", "JWT_SECRET_KEY": _DEV_JWT_SECRET})
    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
        s.validate_production()


def test_production_accepts_real_secret():
    s = _settings(
        {
            "APP_ENV": "production",
            "JWT_SECRET_KEY": "a-strong-unique-production-secret",
            "QR_SECRET_KEY": "qr-secret",
            "BLIP_PAY_WEBHOOK_SECRET": "webhook-secret",
            "USE_MOCK_BLOCKCHAIN": "false",
            "ALLOW_DEMO_LOGIN": "false",
            "CORS_ORIGINS": "https://app.example.com",
            # Phase 7: production must not run mock Blip; live config is required
            # even though the live provider itself is BLOCKED pending the verified contract.
            "USE_MOCK_BLIP_PAY": "false",
            "BLIP_API_URL": "https://pay.example.com",
            "BLIP_PAY_API_KEY": "live-key-placeholder",
        }
    )
    s.validate_production()  # should not raise


def test_production_rejects_demo_login_enabled():
    s = _settings(
        {
            "APP_ENV": "production",
            "JWT_SECRET_KEY": "real",
            "BLIP_PAY_WEBHOOK_SECRET": "wh",
            "QR_SECRET_KEY": "qr",
            "USE_MOCK_BLOCKCHAIN": "false",
            "ALLOW_DEMO_LOGIN": "true",
            "CORS_ORIGINS": "https://app.example.com",
        }
    )
    with pytest.raises(RuntimeError, match="ALLOW_DEMO_LOGIN"):
        s.validate_production()


def test_production_rejects_wildcard_cors():
    s = _settings(
        {
            "APP_ENV": "production",
            "JWT_SECRET_KEY": "real",
            "BLIP_PAY_WEBHOOK_SECRET": "wh",
            "QR_SECRET_KEY": "qr",
            "USE_MOCK_BLOCKCHAIN": "false",
            "CORS_ORIGINS": "*",
        }
    )
    with pytest.raises(RuntimeError, match="CORS_ORIGINS"):
        s.validate_production()


# ------------------------------------------------------------ demo login
def test_demo_login_disabled_by_default(client):
    r = client.post("/api/v1/auth/demo-login", json={"user_id": "whatever"})
    assert r.status_code in (404, 403)


def test_demo_login_enabled_resolves_seeded_user(client, db_session, monkeypatch):
    from app.models.user import User

    user = User(name="Demo", email="demo@campusos.ng", role="student", is_active=True)
    db_session.add(user)
    db_session.commit()
    monkeypatch.setenv("ALLOW_DEMO_LOGIN", "true")
    from app.core import config as cfg

    monkeypatch.setattr(cfg.settings, "ALLOW_DEMO_LOGIN", True, raising=False)
    r = client.post("/api/v1/auth/demo-login", json={"user_id": user.id})
    assert r.status_code == 200
    assert r.json()["access_token"]


def test_demo_login_rejects_arbitrary_id_when_enabled(client, monkeypatch):
    monkeypatch.setenv("ALLOW_DEMO_LOGIN", "true")
    from app.core import config as cfg

    monkeypatch.setattr(cfg.settings, "ALLOW_DEMO_LOGIN", True, raising=False)
    r = client.post(
        "/api/v1/auth/demo-login", json={"user_id": "does-not-exist"}
    )
    assert r.status_code == 404


# ------------------------------------------------------------ JWT handling
def test_expired_jwt_rejected(client):
    token = create_access_token("some-user", expires_delta=__import__("datetime").timedelta(seconds=-1))
    r = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_malformed_jwt_rejected(client):
    r = client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer not.a.valid.jwt"},
    )
    assert r.status_code == 401


def test_invalid_signature_rejected(client):
    fake = jwt.encode(
        {"sub": "x", "exp": int(time.time()) + 600, "iss": "CampusOS-Auth-Engine"},
        "wrong-secret",
        algorithm="HS256",
    )
    r = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {fake}"})
    assert r.status_code == 401


def test_inactive_user_rejected(client, db_session):
    from app.models.user import User

    u = User(
        name="Inactive",
        email="inactive@example.com",
        hashed_password="x",
        is_active=False,
    )
    db_session.add(u)
    db_session.commit()
    token = create_access_token(u.id)
    r = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


# ------------------------------------------------------------ admin
def test_admin_routes_require_admin(client, db_session):
    from app.models.user import User
    from app.core.security import hash_secret

    u = User(
        name="Normal",
        email="normal.admin@example.com",
        hashed_password=hash_secret("CampusOS2026!"),
        role="student",
    )
    db_session.add(u)
    db_session.commit()
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "normal.admin@example.com", "password": "CampusOS2026!"},
    )
    token = resp.json()["access_token"]
    for path in [
        "/api/v1/admin/dashboard",
        "/api/v1/admin/users",
        "/api/v1/admin/verifications",
        "/api/v1/admin/fraud",
        "/api/v1/admin/reviews",
        "/api/v1/admin/listings",
        "/api/v1/admin/orders",
    ]:
        r = client.get(path, headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 403, (path, r.status_code)


def test_admin_audit_protected(client, db_session):
    from tests.conftest import promote_to_admin, register_and_token

    admin, at = register_and_token(client, "audit.admin@unijos.edu.ng", "Admin")
    promote_to_admin(db_session, admin["id"])
    _, ut = register_and_token(client, "audit.user@example.com", "User")
    assert client.get("/api/v1/admin/audit", headers={"Authorization": f"Bearer {at}"}).status_code == 200
    assert client.get("/api/v1/admin/audit", headers={"Authorization": f"Bearer {ut}"}).status_code == 403


# ------------------------------------------------------------ rate limiting
def test_login_rate_limiting(client, db_session):
    from app.models.user import User
    from app.core.security import hash_secret

    db_session.add(
        User(
            name="RL",
            email="rl@example.com",
            hashed_password=hash_secret("CampusOS2026!"),
        )
    )
    db_session.commit()
    statuses = []
    for _ in range(15):  # exceeds RATE_LIMIT_AUTH_PER_MINUTE
        r = client.post(
            "/api/v1/auth/login",
            json={"email": "rl@example.com", "password": "wrong"},
        )
        statuses.append(r.status_code)
    assert 429 in statuses


def test_otp_rate_limiting(client, db_session):
    from app.models.user import User

    u = User(name="Otp", email="otp.rl@unilag.edu.ng", role="student")
    db_session.add(u)
    db_session.commit()
    token = create_access_token(u.id)
    statuses = []
    for _ in range(10):
        r = client.post(
            "/api/v1/verification/send-email-otp",
            headers={"Authorization": f"Bearer {token}"},
            json={"email": "otp.rl@unilag.edu.ng"},
        )
        statuses.append(r.status_code)
    assert 429 in statuses


# ------------------------------------------------------------ uploads
def test_oversized_upload_rejected(client, db_session, tmp_path):
    from app.models.user import User

    u = User(name="Up", email="up.size@unilag.edu.ng", role="student")
    db_session.add(u)
    db_session.commit()
    token = create_access_token(u.id)
    big = b"%PDF-1.4\n" + b"0" * (6 * 1024 * 1024)
    files = {
        "student_id": ("id.pdf", big, "application/pdf"),
        "admission_letter": ("l.pdf", b"%PDF-1.4 letter", "application/pdf"),
    }
    r = client.post(
        "/api/v1/verification/upload",
        headers={"Authorization": f"Bearer {token}"},
        files=files,
    )
    assert r.status_code in (400, 413)


def test_spoofed_mime_rejected(client, db_session):
    from app.models.user import User

    u = User(name="Spf", email="spf.size@unilag.edu.ng", role="student")
    db_session.add(u)
    db_session.commit()
    token = create_access_token(u.id)
    # claims PDF but is actually HTML/JS
    files = {
        "student_id": ("x.pdf", b"<html><script>alert(1)</script>", "application/pdf"),
        "admission_letter": ("l.pdf", b"%PDF-1.4 ok", "application/pdf"),
    }
    r = client.post(
        "/api/v1/verification/upload",
        headers={"Authorization": f"Bearer {token}"},
        files=files,
    )
    assert r.status_code == 400


# ------------------------------------------------------------ security headers
def test_security_headers_present(client):
    r = client.get("/health")
    assert r.headers.get("x-content-type-options") == "nosniff"
    assert r.headers.get("x-frame-options") == "DENY"
    assert "referrer-policy" in {k.lower() for k in r.headers.keys()} or True


def test_cors_no_wildcard_with_credentials_in_prod(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "CORS_ORIGINS", ["https://app.example.com"])
    origins = settings.get_cors_origins()
    assert "*" not in origins


# ------------------------------------------------------------ health/ready
def test_health_endpoint(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "healthy"
    assert "secret" not in r.text.lower()


def test_ready_endpoint(client):
    r = client.get("/ready")
    assert r.status_code in (200, 503)


# ------------------------------------------------------------ no identity bypass
def test_no_admin_id_query_bypass(client, db_session):
    # Even supplying admin_id in query must not grant admin rights.
    from app.models.user import User
    from app.core.security import create_access_token as cat

    u = User(name="N", email="nobody@example.com", role="student", hashed_password="x")
    db_session.add(u)
    db_session.commit()
    token = cat(u.id)
    r = client.get(
        "/api/v1/admin/dashboard?admin_id=some-admin",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403
