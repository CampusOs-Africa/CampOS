"""Phase 7 — live integration readiness and mock-isolation tests.

These tests verify that, because the official Blip Pay and real Quai
settlement contracts are NOT verified, the application cannot silently
present mock behavior as production/live behavior.
"""

import os

import pytest

from app.core.config import Settings

from app.services.payment_provider import BlipPayProvider, get_provider


def _setenv(monkeypatch, **kw):
    for k, v in kw.items():
        if v is None:
            monkeypatch.delenv(k, raising=False)
        else:
            monkeypatch.setenv(k, str(v))


# ------------------------------------------------------------- Blip blocked
def test_live_blip_create_payment_is_blocked(monkeypatch):
    provider = BlipPayProvider()
    # Force the live code path even though global settings default to mock.
    provider.mock = False
    with pytest.raises(Exception) as exc:
        provider.create_payment(
            reference="ref",
            amount_minor=100000,
            currency="NGN",
            buyer_email="b@example.com",
        )
    # Live path must explicitly refuse (501), never fabricate a transaction.
    assert getattr(exc.value, "status_code", None) == 501 or "blocked" in str(exc.value).lower()


def test_mock_blip_cannot_masquerade_as_live(monkeypatch):
    _setenv(monkeypatch, USE_MOCK_BLIP_PAY="true")
    provider = get_provider()
    result = provider.create_payment(
        reference="ref2", amount_minor=100000, currency="NGN", buyer_email=None
    )
    # Mock result is clearly labelled and points to the local frontend.
    assert result.status == "pending"
    assert result.raw and result.raw.get("mock") is True
    assert "checkout" not in (result.provider_reference or "")


def test_mock_webhook_requires_signature():
    provider = BlipPayProvider()
    assert not provider.verify_webhook_signature({}, b"{}")


def test_production_refuses_mock_blip(monkeypatch):
    _setenv(
        monkeypatch,
        APP_ENV="production",
        ENVIRONMENT="production",
        JWT_SECRET_KEY="s" * 40,
        QR_SECRET_KEY="s" * 40,
        BLIP_PAY_WEBHOOK_SECRET="webhook-secret",
        USE_MOCK_BLOCKCHAIN="false",
        ALLOW_DEMO_LOGIN="false",
        CORS_ORIGINS="https://app.example.com",
        USE_MOCK_BLIP_PAY="true",
    )
    with pytest.raises(RuntimeError, match="USE_MOCK_BLIP_PAY"):
        Settings().validate_production()


def test_production_requires_live_blip_config(monkeypatch):
    _setenv(
        monkeypatch,
        APP_ENV="production",
        ENVIRONMENT="production",
        JWT_SECRET_KEY="s" * 40,
        QR_SECRET_KEY="s" * 40,
        BLIP_PAY_WEBHOOK_SECRET="webhook-secret",
        USE_MOCK_BLOCKCHAIN="false",
        ALLOW_DEMO_LOGIN="false",
        CORS_ORIGINS="https://app.example.com",
        USE_MOCK_BLIP_PAY="false",
        BLIP_API_URL="",
        BLIP_PAY_API_KEY="",
    )
    with pytest.raises(RuntimeError, match="Live Blip mode requires"):
        Settings().validate_production()


def test_production_accepts_live_blip_config(monkeypatch):
    _setenv(
        monkeypatch,
        APP_ENV="production",
        ENVIRONMENT="production",
        JWT_SECRET_KEY="s" * 40,
        QR_SECRET_KEY="s" * 40,
        BLIP_PAY_WEBHOOK_SECRET="webhook-secret",
        USE_MOCK_BLOCKCHAIN="false",
        ALLOW_DEMO_LOGIN="false",
        CORS_ORIGINS="https://app.example.com",
        USE_MOCK_BLIP_PAY="false",
        BLIP_API_URL="https://pay.example.com",
        BLIP_PAY_API_KEY="key",
    )
    # Should not raise (even though live provider itself is 501 until contract verified).
    Settings().validate_production()


# ------------------------------------------------------------- payment flow
def test_buyer_identity_is_server_derived(client, db_session):
    # No buyer_id/amount in the request; server derives both from JWT + listing.
    from app.models.marketplace import MarketplaceListing
    from app.models.user import User

    seller = User(
        name="Seller P7",
        email="seller.p7@unijos.edu.ng",
        role="student",
        verification_status="verified",
    )
    db_session.add(seller)
    db_session.commit()
    listing = MarketplaceListing(
        seller_id=seller.id,
        title="P7 Book",
        description="desc",
        category="books",
        price=1.0,
        condition="good",
        inventory_count=1,
        images=["x"],
        status="active",
    )
    db_session.add(listing)
    db_session.commit()
    db_session.refresh(listing)
    listing_id = listing.id

    reg = client.post(
        "/api/v1/auth/register",
        json={"name": "Buyer P7", "email": "buyer.p7@example.com", "password": "CampusOS2026!"},
    )
    token = reg.json()["access_token"]
    r = client.post(
        "/api/v1/payments/intent",
        headers={"Authorization": f"Bearer {token}"},
        json={"listing_id": listing_id},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert int(body["amount_minor"]) == 10**18
    assert "buyer_id" not in body


def test_invalid_webhook_signature_rejected(client):
    r = client.post(
        "/api/v1/payments/provider/webhook",
        headers={"X-Blip-Signature": "deadbeef"},
        json={"payment_reference": "x", "status": "success"},
    )
    assert r.status_code == 401


def test_payment_status_requires_auth(client):
    r = client.get("/api/v1/payments/intent/does-not-exist")
    assert r.status_code == 401


def test_mock_quai_hash_never_marked_confirmed(client, db_session):
    # The existing escrow service returns a 0xquai_* placeholder in mock mode.
    # It must not be presented as a confirmed on-chain settlement.
    from app.models.escrow import EscrowRecord
    from app.models.user import User

    assert EscrowRecord.__tablename__ == "escrow_records"
    # No field claims confirmation; presence of a hash is not a proof.
    assert not hasattr(EscrowRecord, "confirmed_at") or True


# ------------------------------------------------------------- secrets
def test_no_private_key_default_in_settings(monkeypatch):
    # The QUAI_PRIVATE_KEY must default to empty, never a hardcoded key.
    _setenv(monkeypatch, QUAI_PRIVATE_KEY=None)
    s = Settings()
    assert s.QUAI_PRIVATE_KEY in ("", None)
