"""
Complete End-to-End Integration Test for CampusOS (12-stage lifecycle).

All authenticated actions use real JWTs obtained via /api/v1/auth/register.
Client-supplied identity parameters (actor_id, buyer_id, reviewer_id, etc.)
are retained in request bodies but the backend derives identity from the JWT.
"""

from tests.conftest import promote_to_admin, register_and_token


def test_complete_e2e_campusos_flow(client, db_session):
    # STEP 1: verified seller & buyer, admin approves.
    admin, atoken = register_and_token(client, "a.admin@unijos.edu.ng", "Prof. Admin")
    promote_to_admin(db_session, admin["id"])
    aauth = {"Authorization": f"Bearer {atoken}"}

    seller, stoken = register_and_token(
        client, "amina.seller.e2e@unijos.edu.ng", "Amina Bello (Seller)"
    )
    seller_id = seller["id"]
    sauth = {"Authorization": f"Bearer {stoken}"}

    seller_verif = client.post(
        "/api/v1/verification/upload",
        headers=sauth,
        data={"university_email": "amina.seller.e2e@unijos.edu.ng"},
        files=[
            ("student_id", ("id.pdf", b"%PDF-1.4 mock", "application/pdf")),
            ("admission_letter", ("letter.pdf", b"%PDF-1.4 mock", "application/pdf")),
        ],
    ).json()
    approve_seller = client.post(
        f"/api/v1/verification/admin/{seller_verif['id']}/approve", headers=aauth
    )
    assert approve_seller.status_code == 200

    buyer, btoken = register_and_token(
        client, "chidi.buyer.e2e@unijos.edu.ng", "Chidi Okafor (Buyer)"
    )
    buyer_id = buyer["id"]
    bauth = {"Authorization": f"Bearer {btoken}"}

    buyer_verif = client.post(
        "/api/v1/verification/upload",
        headers=bauth,
        data={"university_email": "chidi.buyer.e2e@unijos.edu.ng"},
        files=[
            ("student_id", ("id.pdf", b"%PDF-1.4 mock", "application/pdf")),
            ("admission_letter", ("letter.pdf", b"%PDF-1.4 mock", "application/pdf")),
        ],
    ).json()
    client.post(
        f"/api/v1/verification/admin/{buyer_verif['id']}/approve", headers=aauth
    )

    seller_db = client.get(f"/api/v1/users/{seller_id}").json()
    buyer_db = client.get(f"/api/v1/users/{buyer_id}").json()
    assert seller_db["verification_status"] == "verified"
    assert seller_db["trust_score"] == 60
    assert buyer_db["verification_status"] == "verified"

    # Wallet connect & balances (JWT identifies the user).
    client.post(
        "/api/v1/wallet/connect",
        headers=sauth,
        json={
            "user_id": seller_id,
            "wallet_address": "0x1111111111111111111111111111111111111111",
            "signature": "0xmock_signature_hex_65_bytes",
            "message": "CampusOS Web3 Authentication Challenge",
        },
    )
    seller_wallet = client.get("/api/v1/wallet/balance", headers=sauth).json()
    assert seller_wallet["balance_quai"] == 25.5

    client.post(
        "/api/v1/wallet/connect",
        headers=bauth,
        json={
            "user_id": buyer_id,
            "wallet_address": "0x2222222222222222222222222222222222222222",
            "signature": "0xmock_signature_hex_65_bytes",
            "message": "CampusOS Web3 Authentication Challenge",
        },
    )
    buyer_wallet = client.get("/api/v1/wallet/balance", headers=bauth).json()
    assert buyer_wallet["balance_quai"] == 25.5

    # STEP 2: seller creates listing.
    listing_payload = {
        "seller_id": seller_id,
        "title": "Engineering Mathematics Vol 2 (10th Ed)",
        "description": "Mint condition engineering textbook with practice workbook.",
        "category": "books",
        "price": 10000.0,
        "condition": "like_new",
        "inventory_count": 1,
        "images": ["https://res.cloudinary.com/test/eng_math_v2.jpg"],
    }
    create_listing_res = client.post(
        "/api/v1/marketplace/listings", json=listing_payload, headers=sauth
    )
    assert create_listing_res.status_code == 201
    listing = create_listing_res.json()
    listing_id = listing["id"]
    assert listing["status"] == "active"
    assert listing["seller_verified"] is True
    assert listing["seller_trust_score"] == 65

    # STEP 3: public browsing.
    assert client.get(f"/api/v1/marketplace/listings/{listing_id}").status_code == 200
    catalog = client.get("/api/v1/marketplace/listings?category=books").json()
    assert any(i["id"] == listing_id for i in catalog)
    seller_profile = client.get(f"/api/v1/marketplace/sellers/{seller_id}").json()
    assert seller_profile["user_id"] == seller_id

    # STEP 4: buyer initiates checkout (buyer from JWT).
    checkout_payload = {"buyer_id": buyer_id, "listing_id": listing_id, "amount": 10000.0}
    checkout_res = client.post(
        "/api/v1/payments/initiate", json=checkout_payload, headers=bauth
    )
    assert checkout_res.status_code == 201
    checkout_data = checkout_res.json()
    order_id = checkout_data["order_id"]
    payment_ref = checkout_data["payment_reference"]
    assert payment_ref.startswith("blip_pay_")

    # Buyer can read their own order.
    assert client.get(f"/api/v1/orders/{order_id}", headers=bauth).status_code == 200

    dup_res = client.post(
        "/api/v1/payments/initiate", json=checkout_payload, headers=bauth
    )
    assert dup_res.status_code == 201
    assert dup_res.json()["order_id"] == order_id

    # STEP 5: webhook (server-to-server, HMAC, no JWT).
    webhook_res = client.post(
        "/api/v1/payments/webhook",
        headers={"X-Blip-Signature": "mock_sig_e2e_valid"},
        json={"payment_reference": payment_ref, "status": "success", "amount": 10000.0},
    )
    assert webhook_res.status_code == 200
    updated_order = webhook_res.json()
    assert updated_order["status"] == "escrow_locked"

    records = client.get(f"/api/v1/payments/records/order/{order_id}").json()
    assert any(r["status"] == "successful" for r in records)

    # STEP 6/7: escrow created by webhook; buyer deposits.
    escrow_data = client.get(f"/api/v1/escrow/{order_id}", headers=bauth).json()
    assert escrow_data["buyer_id"] == buyer_id
    assert escrow_data["seller_id"] == seller_id

    deposit_res = client.post(
        "/api/v1/escrow/deposit",
        headers=bauth,
        json={"order_id": order_id, "actor_id": buyer_id},
    )
    assert deposit_res.status_code == 200
    assert deposit_res.json()["state"] == "FUNDED"
    assert client.get(f"/api/v1/orders/{order_id}", headers=bauth).json()["status"] == "escrow_funded"

    # STEP 8: seller ships.
    shipment_res = client.post(
        f"/api/v1/orders/{order_id}/confirm-shipment", headers=sauth
    )
    assert shipment_res.status_code == 200
    assert shipment_res.json()["status"] == "shipped_pending_delivery"

    # STEP 9: buyer confirms delivery.
    delivery_res = client.post(
        f"/api/v1/orders/{order_id}/confirm-delivery", headers=bauth
    )
    assert delivery_res.status_code == 200
    assert delivery_res.json()["status"] == "delivered_pending_release"

    # STEP 10: buyer releases escrow.
    release_res = client.post(
        f"/api/v1/orders/{order_id}/release-escrow", headers=bauth
    )
    assert release_res.status_code == 200
    assert release_res.json()["status"] == "completed"
    assert client.get(f"/api/v1/escrow/{order_id}", headers=bauth).json()["state"] == "COMPLETED"
    assert client.get(f"/api/v1/marketplace/listings/{listing_id}").json()["status"] == "sold"

    buyer_txs = client.get("/api/v1/wallet/history", headers=bauth).json()
    seller_txs = client.get("/api/v1/wallet/history", headers=sauth).json()
    assert any("Marketplace purchase" in (tx.get("note") or "") and tx["type"] == "send" for tx in buyer_txs)
    assert any("Marketplace sale" in (tx.get("note") or "") and tx["type"] == "receive" for tx in seller_txs)

    # STEP 11: trust + review (reviewer from JWT).
    assert client.get(f"/api/v1/users/{seller_id}").json()["trust_score"] == 70
    review_res = client.post(
        "/api/v1/reviews/",
        headers=bauth,
        json={
            "order_id": order_id,
            "reviewer_id": buyer_id,
            "reviewee_id": seller_id,
            "rating": 5,
            "comment": "Outstanding seller!",
        },
    )
    assert review_res.status_code == 201
    assert client.get(f"/api/v1/users/{seller_id}").json()["trust_score"] == 72

    # STEP 12: order history (scoped to authenticated user).
    buyer_history = client.get("/api/v1/orders/history?role=buyer", headers=bauth).json()
    seller_history = client.get("/api/v1/orders/history?role=seller", headers=sauth).json()
    assert any(o["id"] == order_id and o["status"] == "completed" for o in buyer_history)
    assert any(o["id"] == order_id and o["status"] == "completed" for o in seller_history)

    seller_reviews = client.get(f"/api/v1/reviews/user/{seller_id}").json()
    assert len(seller_reviews) == 1
    assert seller_reviews[0]["rating"] == 5
