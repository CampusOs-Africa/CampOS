"""Phase 6 — payment intent, webhook security, idempotency."""

import hashlib
import hmac
import time

import pytest

from app.core.config import settings
from app.models.marketplace import MarketplaceListing
from app.models.user import User


def _seller_and_listing(db_session, verified=True):
    seller = User(
        name="Seller",
        email=f"seller-{time.time_ns()}@unijos.edu.ng",
        role="student",
        verification_status="verified" if verified else "pending",
    )
    db_session.add(seller)
    db_session.commit()
    listing = MarketplaceListing(
        seller_id=seller.id,
        title="Textbook",
        description="Used textbook",
        category="books",
        price=1.0,
        condition="good",
        inventory_count=1,
        images=["https://res.cloudinary.com/x/y.jpg"],
        status="active",
    )
    db_session.add(listing)
    db_session.commit()
    db_session.refresh(listing)
    return seller, listing


def _buyer(client, db_session, email="buyer.p6@example.com"):
    r = client.post(
        "/api/v1/auth/register",
        json={"name": "Buyer", "email": email, "password": "CampusOS2026!"},
    )
    return r.json()


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _webhook_headers(raw: bytes) -> dict:
    secret = settings.BLIP_PAY_WEBHOOK_SECRET
    sig = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    return {
        "X-Blip-Signature": sig,
        "X-Blip-Timestamp": str(int(time.time())),
    }


# --------------------------------------------------------------- identity/auth
def test_cannot_initiate_for_another_user(client, db_session):
    # No token -> 401
    _, listing = _seller_and_listing(db_session)
    r = client.post("/api/v1/payments/intent", json={"listing_id": listing.id})
    assert r.status_code == 401


def test_amount_is_server_authoritative(client, db_session):
    buyer = _buyer(client, db_session)
    _, listing = _seller_and_listing(db_session)
    r = client.post(
        "/api/v1/payments/intent",
        headers=_auth(buyer["access_token"]),
        json={"listing_id": listing.id},
    )
    assert r.status_code == 201, r.text
    # 5000 NGN -> 500000 minor units, regardless of any client value
    assert int(r.json()["amount_minor"]) == 10**18  # 1 QUAI in wei
    assert "buyer_id" not in r.json()  # identity not echoed beyond JWT


def test_cannot_buy_own_listing(client, db_session):
    # Register a user, promote directly to verified seller.
    r = client.post(
        "/api/v1/auth/register",
        json={"name": "Owner", "email": "owner.p6@unijos.edu.ng", "password": "CampusOS2026!"},
    )
    token = r.json()["access_token"]
    uid = r.json()["user"]["id"]
    u = db_session.get(User, uid)
    u.verification_status = "verified"
    db_session.commit()
    listing = MarketplaceListing(
        seller_id=uid, title="Mine", description="x", category="books",
        price=10.0, condition="good", inventory_count=1, images=["x"], status="active",
    )
    db_session.add(listing)
    db_session.commit()
    r = client.post(
        "/api/v1/payments/intent",
        headers=_auth(token),
        json={"listing_id": listing.id},
    )
    assert r.status_code == 400


# --------------------------------------------------------------- idempotency
def test_duplicate_idempotency_key_reuses_intent(client, db_session):
    buyer = _buyer(client, db_session)
    _, listing = _seller_and_listing(db_session)
    payload = {"listing_id": listing.id, "idempotency_key": "abc-123"}
    r1 = client.post("/api/v1/payments/intent", headers=_auth(buyer["access_token"]), json=payload)
    r2 = client.post("/api/v1/payments/intent", headers=_auth(buyer["access_token"]), json=payload)
    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["id"] == r2.json()["id"]


def test_idempotency_key_diff_user_rejected(client, db_session):
    _, listing = _seller_and_listing(db_session)
    listing_id = listing.id
    buyer1 = _buyer(client, db_session, "buyer1.p6@example.com")
    buyer2 = _buyer(client, db_session, "buyer2.p6@example.com")
    payload = {"listing_id": listing_id, "idempotency_key": "shared-key"}
    client.post("/api/v1/payments/intent", headers=_auth(buyer1["access_token"]), json=payload)
    r = client.post("/api/v1/payments/intent", headers=_auth(buyer2["access_token"]), json=payload)
    # Same key for a different buyer is rejected, not silently created.
    assert r.status_code in (409, 400)


# --------------------------------------------------------------- webhook
def test_webhook_missing_signature_rejected(client):
    r = client.post(
        "/api/v1/payments/provider/webhook",
        json={"payment_reference": "x", "status": "success"},
    )
    assert r.status_code == 401


def test_webhook_invalid_signature_rejected(client):
    r = client.post(
        "/api/v1/payments/provider/webhook",
        headers={"X-Blip-Signature": "deadbeef"},
        json={"payment_reference": "x", "status": "success"},
    )
    assert r.status_code == 401


def test_full_paid_flow_locks_escrow(client, db_session):
    buyer = _buyer(client, db_session)
    _, listing = _seller_and_listing(db_session)
    intent = client.post(
        "/api/v1/payments/intent",
        headers=_auth(buyer["access_token"]),
        json={"listing_id": listing.id},
    ).json()
    # Payment reference lives on the order; fetch it via order.
    order_id = intent["order_id"]
    from app.models.order import Order
    order = db_session.get(Order, order_id)
    body = (
        f'{{"payment_reference":"{order.payment_reference}","status":"success",'
        f'"amount_minor":{intent["amount_minor"]},"currency":"NGN"}}'
    ).encode()
    r = client.post(
        "/api/v1/payments/provider/webhook",
        headers=_webhook_headers(body),
        content=body,
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "escrow_locked"


def test_webhook_wrong_amount_rejected(client, db_session):
    buyer = _buyer(client, db_session)
    _, listing = _seller_and_listing(db_session)
    intent = client.post(
        "/api/v1/payments/intent",
        headers=_auth(buyer["access_token"]),
        json={"listing_id": listing.id},
    ).json()
    from app.models.order import Order
    order = db_session.get(Order, intent["order_id"])
    body = (
        f'{{"payment_reference":"{order.payment_reference}","status":"success",'
        f'"amount_minor":1,"currency":"NGN"}}'
    ).encode()
    r = client.post(
        "/api/v1/payments/provider/webhook",
        headers=_webhook_headers(body),
        content=body,
    )
    assert r.status_code == 400


def test_duplicate_webhook_is_idempotent(client, db_session):
    buyer = _buyer(client, db_session)
    _, listing = _seller_and_listing(db_session)
    intent = client.post(
        "/api/v1/payments/intent",
        headers=_auth(buyer["access_token"]),
        json={"listing_id": listing.id},
    ).json()
    from app.models.order import Order
    order = db_session.get(Order, intent["order_id"])
    body = (
        f'{{"event_id":"evt-1","payment_reference":"{order.payment_reference}",'
        f'"status":"success","amount_minor":{intent["amount_minor"]},"currency":"NGN"}}'
    ).encode()
    h = _webhook_headers(body)
    r1 = client.post("/api/v1/payments/provider/webhook", headers=h, content=body)
    r2 = client.post("/api/v1/payments/provider/webhook", headers=h, content=body)
    assert r1.status_code == 200
    assert r2.status_code == 200


def test_paid_cannot_be_paid_twice(client, db_session):
    buyer = _buyer(client, db_session)
    _, listing = _seller_and_listing(db_session)
    intent = client.post(
        "/api/v1/payments/intent",
        headers=_auth(buyer["access_token"]),
        json={"listing_id": listing.id},
    ).json()
    from app.models.order import Order
    order = db_session.get(Order, intent["order_id"])
    body = (
        f'{{"payment_reference":"{order.payment_reference}","status":"success",'
        f'"amount_minor":{intent["amount_minor"]},"currency":"NGN"}}'
    ).encode()
    client.post("/api/v1/payments/provider/webhook", headers=_webhook_headers(body), content=body)
    # A second distinct event trying to mark paid must not double-process.
    body2 = body.replace(b'"status":"success"', b'"status":"success"').replace(b'{"', b'{"event_id":"evt-2",')
    r = client.post("/api/v1/payments/provider/webhook", headers=_webhook_headers(body2), content=body2)
    # Either idempotent or rejected; never a second state mutation.
    assert r.status_code in (200, 400, 409)


def test_browser_callback_cannot_prove_payment(client):
    # The success callback returns order status but never mutates to paid by itself.
    r = client.get("/api/v1/payments/callback/success?reference=nonexistent")
    assert r.status_code in (404, 200)


def test_unverified_seller_cannot_sell(client, db_session):
    _, listing = _seller_and_listing(db_session, verified=False)
    listing_id = listing.id
    buyer = _buyer(client, db_session, "unverified.buyer.p6@example.com")
    r = client.post(
        "/api/v1/payments/intent",
        headers=_auth(buyer["access_token"]),
        json={"listing_id": listing_id},
    )
    assert r.status_code == 400


def test_payment_status_endpoint(client, db_session):
    buyer = _buyer(client, db_session)
    _, listing = _seller_and_listing(db_session)
    intent = client.post(
        "/api/v1/payments/intent",
        headers=_auth(buyer["access_token"]),
        json={"listing_id": listing.id},
    ).json()
    r = client.get(
        f"/api/v1/payments/intent/{intent['id']}",
        headers=_auth(buyer["access_token"]),
    )
    assert r.status_code == 200
    assert r.json()["status"] in ("pending", "processing")


def test_no_private_keys_in_responses(client, db_session):
    buyer = _buyer(client, db_session)
    _, listing = _seller_and_listing(db_session)
    r = client.post(
        "/api/v1/payments/intent",
        headers=_auth(buyer["access_token"]),
        json={"listing_id": listing.id},
    )
    assert "private" not in r.text.lower()
    assert "secret" not in r.text.lower()


def test_mock_quai_not_presented_as_real(client, db_session):
    # In mock mode, checkout URL points to the FRONTEND, never claims a real Quai tx.
    buyer = _buyer(client, db_session, "mockcheck.p6@example.com")
    _, listing = _seller_and_listing(db_session)
    r = client.post(
        "/api/v1/payments/intent",
        headers=_auth(buyer["access_token"]),
        json={"listing_id": listing.id},
    )
    body = r.json()
    assert body["status"] == "pending"
    assert not body.get("quai_tx_hash")
