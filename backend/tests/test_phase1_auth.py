"""Phase 1 authentication tests (JWT register/login/me + seller gate)."""

from fastapi.testclient import TestClient


def _register(client: TestClient, email: str = "student@example.com", password: str = "CampusOS2026!"):
    return client.post(
        "/api/v1/auth/register",
        json={"name": "Test Student", "email": email, "password": password},
    )


def test_register_accepts_any_valid_email_and_returns_jwt(client: TestClient):
    # Non-institutional email must be accepted at signup.
    resp = _register(client, email="anyone@gmail.com")
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["email"] == "anyone@gmail.com"
    # Password hash must never be returned.
    assert "hashed_password" not in body["user"]


def test_register_requires_password_min_length(client: TestClient):
    resp = client.post(
        "/api/v1/auth/register",
        json={"name": "Short PW", "email": "short@example.com", "password": "123"},
    )
    assert resp.status_code == 422


def test_duplicate_email_rejected(client: TestClient):
    _register(client, email="dup@example.com")
    resp = _register(client, email="dup@example.com")
    assert resp.status_code == 409


def test_login_with_correct_password_returns_jwt(client: TestClient):
    _register(client, email="login@example.com", password="Secret123!")
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "Secret123!"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["access_token"]


def test_login_with_wrong_password_is_401(client: TestClient):
    _register(client, email="bad@example.com")
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "bad@example.com", "password": "wrong-password"},
    )
    assert resp.status_code == 401


def test_me_requires_valid_jwt(client: TestClient):
    assert client.get("/api/v1/auth/me").status_code == 401
    token = _register(client, email="me@example.com").json()["access_token"]
    resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@example.com"


def test_forged_jwt_is_rejected(client: TestClient):
    resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not.a.real.token"},
    )
    assert resp.status_code == 401


def _make_verified_seller(
    client: TestClient, db_session, email: str = "seller@example.com"
):
    _register(client, email=email)
    from app.models.user import User

    user = db_session.query(User).filter(User.email == email).first()
    assert user is not None
    user.verification_status = "verified"
    db_session.commit()
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "CampusOS2026!"},
    ).json()["access_token"]


def test_unverified_user_cannot_create_listing_even_with_seller_id(client: TestClient, db_session):
    token = _register(client, email="buyer@example.com").json()["access_token"]
    payload = {
        "seller_id": "00000000-0000-0000-0000-000000000000",  # attempt to impersonate
        "title": "Fake listing",
        "description": "Should be blocked",
        "category": "books",
        "price": 1.0,
        "condition": "new",
        "inventory_count": 1,
        "images": ["https://res.cloudinary.com/x/y.jpg"],
    }
    # No token -> 401
    assert client.post("/api/v1/marketplace/listings", json=payload).status_code == 401
    # Token present but unverified, and trying another seller_id -> 403
    resp = client.post(
        "/api/v1/marketplace/listings",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
    # seller_id is required by the schema; with their own id an unverified
    # user is still rejected by the verified-student gate (403).
    me = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    ).json()
    payload["seller_id"] = me["id"]
    resp = client.post(
        "/api/v1/marketplace/listings",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_verified_user_can_create_listing_with_jwt(client: TestClient, db_session):
    token = _make_verified_seller(client, db_session, email="verified@example.com")
    me = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    ).json()
    payload = {
        "seller_id": me["id"],
        "title": "Real textbook",
        "description": "Good condition textbook",
        "category": "books",
        "price": 2.5,
        "condition": "like_new",
        "inventory_count": 1,
        "images": ["https://res.cloudinary.com/x/y.jpg"],
    }
    resp = client.post(
        "/api/v1/marketplace/listings",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    # Server must have set seller_id from the JWT, not the client value.
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}).json()
    assert body["seller_id"] == me["id"]


def test_marketplace_browsing_does_not_require_auth(client: TestClient):
    assert client.get("/api/v1/marketplace/listings").status_code == 200
    assert client.get("/api/v1/marketplace/categories").status_code == 200
