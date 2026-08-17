"""Pre-push regression tests for the acceptance fixes."""

import os
import tempfile

from fastapi.testclient import TestClient


def _client_with_fresh_db(tmp_path, monkeypatch):
    db_file = tmp_path / "fresh.db"
    db_url = f"sqlite:///{db_file}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("USE_REDIS_RATE_LIMIT", "false")
    monkeypatch.setenv("ALLOW_DEMO_LOGIN", "true")

    # Import after env is set so the app binds the new DATABASE_URL.
    import importlib
    import app.core.config as cfg
    import app.core.database as db
    import app.main as main

    importlib.reload(cfg)
    importlib.reload(db)
    importlib.reload(main)
    return TestClient(main.app), str(db_file)


def test_fresh_database_does_not_500_on_register(tmp_path, monkeypatch):
    """A brand-new DB must be migrated automatically in development so signup
    does not fail with 'no such table: users'."""
    client, db_file = _client_with_fresh_db(tmp_path, monkeypatch)
    with client:
        # Startup event runs migrations.
        r = client.post(
            "/api/v1/auth/register",
            json={
                "name": "Fresh User",
                "email": "fresh@example.com",
                "password": "CampusOS2026!",
            },
        )
        assert r.status_code == 201, r.text
        assert "access_token" in r.json()


def test_duplicate_email_returns_409(client):
    email = "dupe@example.com"
    body = {"name": "Dupe", "email": email, "password": "CampusOS2026!"}
    r1 = client.post("/api/v1/auth/register", json=body)
    assert r1.status_code == 201
    r2 = client.post("/api/v1/auth/register", json=body)
    assert r2.status_code == 409
    body = r2.json()
    msg = body.get("detail") or body.get("error", {}).get("message", "")
    assert "already exists" in msg.lower()


def test_create_listing_does_not_require_seller_id(client, make_user):
    verified_seller, _, auth_headers = make_user(
        "seller@example.com", verified=True
    )
    """No seller_id in body -> the server derives it from the JWT and the
    verified-seller gate decides (here verified -> 201)."""
    payload = {
        "title": "No Seller ID",
        "description": "Server derives seller identity.",
        "price": 1.0,
        "category": "books",
        "condition": "good",
        "inventory_count": 1,
        "images": ["https://example.com/x.jpg"],
    }
    r = client.post(
        "/api/v1/marketplace/listings", json=payload, headers=auth_headers
    )
    assert r.status_code == 201, r.text
    assert r.json()["seller_id"] == verified_seller["id"]


def test_cannot_impersonate_seller_id(client, make_user):
    verified_seller, _, auth_headers = make_user(
        "seller2@example.com", verified=True
    )
    payload = {
        "seller_id": "00000000-0000-0000-0000-000000000000",
        "title": "Impersonate",
        "description": "Should be rejected.",
        "price": 1.0,
        "category": "books",
        "condition": "good",
        "inventory_count": 1,
        "images": ["https://example.com/x.jpg"],
    }
    r = client.post(
        "/api/v1/marketplace/listings", json=payload, headers=auth_headers
    )
    assert r.status_code == 403


def test_unverified_seller_gets_403_not_422(client, make_user):
    _, _, auth_headers = make_user("unverified@example.com", verified=False)
    payload = {
        "title": "Unverified Listing",
        "description": "Server checks verification, not body validity first.",
        "price": 1.0,
        "category": "books",
        "condition": "good",
        "inventory_count": 1,
        "images": ["https://example.com/x.jpg"],
    }
    r = client.post(
        "/api/v1/marketplace/listings", json=payload, headers=auth_headers
    )
    assert r.status_code == 403


def test_mock_storage_uses_non_production_url(client, make_user):
    _, _, auth_headers = make_user("uploader@example.com", verified=False)
    """Mock document storage must not produce a fake cloudinary.com URL."""
    import io
    files = {
        "student_id": (
            "id.pdf",
            io.BytesIO(b"%PDF-1.4\n%%EOF\n"),
            "application/pdf",
        ),
        "admission_letter": (
            "letter.pdf",
            io.BytesIO(b"%PDF-1.4\n%%EOF\n"),
            "application/pdf",
        ),
    }
    r = client.post(
        "/api/v1/verification/upload",
        files=files,
        data={"university_email": "student@unilag.edu.ng"},
        headers=auth_headers,
    )
    assert r.status_code in (200, 201), r.text
    body = r.text
    assert "cloudinary.com/None" not in body
    assert "mock-storage://" in body


def test_payment_intent_uses_quai_settlement(client, make_user):
    verified_seller, _, auth_headers = make_user(
        "pseller@example.com", verified=True
    )
    # Create a listing as the verified seller.
    listing = client.post(
        "/api/v1/marketplace/listings",
        json={
            "title": "Settle",
            "description": "On-chain settlement test.",
            "price": 1.0,
            "category": "books",
            "condition": "good",
            "inventory_count": 1,
            "images": ["https://example.com/x.jpg"],
        },
        headers=auth_headers,
    ).json()

    # Buyer is a different, registered user.
    buyer = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Buyer",
            "email": "buyer@example.com",
            "password": "CampusOS2026!",
        },
    ).json()
    buyer_headers = {"Authorization": f"Bearer {buyer['access_token']}"}

    r = client.post(
        "/api/v1/payments/intent",
        json={"listing_id": listing["id"]},
        headers=buyer_headers,
    )
    assert r.status_code == 201, r.text
    intent = r.json()
    assert intent["settlement_asset"] == "QUAI"
    assert intent["display_currency"] == "NGN"
    # settlement_amount_wei is present and equals 1 QUAI in wei
    assert int(intent["settlement_amount_wei"]) == 10**18
