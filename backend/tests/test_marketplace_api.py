from tests.conftest import promote_to_admin, register_and_token


def test_complete_marketplace_escrow_and_review_lifecycle(client, db_session):
    # 1. Seller registers, uploads verification, admin approves.
    seller, stoken = register_and_token(
        client, "amina.seller@unijos.edu.ng", "Amina Bello"
    )
    seller_id = seller["id"]
    sauth = {"Authorization": f"Bearer {stoken}"}

    admin, atoken = register_and_token(client, "prof.admin@unijos.edu.ng", "Admin Prof")
    promote_to_admin(db_session, admin["id"])
    aauth = {"Authorization": f"Bearer {atoken}"}

    verif = client.post(
        "/api/v1/verification/upload",
        headers=sauth,
        data={"university_email": "amina.seller@unijos.edu.ng"},
        files=[
            ("student_id", ("id.pdf", b"%PDF-1.4 mock id", "application/pdf")),
            ("admission_letter", ("letter.pdf", b"%PDF-1.4 mock letter", "application/pdf")),
        ],
    ).json()
    client.post(f"/api/v1/verification/admin/{verif['id']}/approve", headers=aauth)

    # 2. Create listing as verified seller (JWT required).
    listing_res = client.post(
        "/api/v1/marketplace/listings",
        headers=sauth,
        json={
            "seller_id": seller_id,
            "title": "Calculus Textbook",
            "description": "Like new calculus volume 1 book",
            "category": "books",
            "price": 5000.0,
            "condition": "like_new",
            "inventory_count": 1,
            "images": ["https://res.cloudinary.com/test/calc.jpg"],
        },
    )
    assert listing_res.status_code == 201
    listing = listing_res.json()
    listing_id = listing["id"]
    assert listing["seller_verified"] is True
    assert listing["seller_trust_score"] == 60

    # 3. Buyer registers and initiates checkout (buyer from JWT).
    buyer, btoken = register_and_token(client, "chidi.buyer@unijos.edu.ng", "Chidi Okafor")
    buyer_id = buyer["id"]
    bauth = {"Authorization": f"Bearer {btoken}"}

    checkout_res = client.post(
        "/api/v1/payments/initiate",
        headers=bauth,
        json={"buyer_id": buyer_id, "listing_id": listing_id, "amount": 5000.0},
    )
    assert checkout_res.status_code == 201
    checkout_data = checkout_res.json()
    order_id = checkout_data["order_id"]
    ref = checkout_data["payment_reference"]

    # 4. Blip webhook is server-to-server (HMAC, no JWT).
    webhook_res = client.post(
        "/api/v1/payments/webhook",
        headers={"X-Blip-Signature": "mock_sig_valid"},
        json={"payment_reference": ref, "status": "success", "amount": 5000.0},
    )
    assert webhook_res.status_code == 200
    order_data = webhook_res.json()
    assert order_data["status"] == "escrow_locked"
    assert order_data["escrow_tx_hash"].startswith("0xquai_escrow_lock_")

    # 5. Buyer confirms delivery, then releases escrow (actor from JWT).
    delivery_res = client.post(f"/api/v1/orders/{order_id}/confirm-delivery", headers=bauth)
    assert delivery_res.status_code == 200
    assert delivery_res.json()["status"] == "delivered_pending_release"

    release_res = client.post(f"/api/v1/orders/{order_id}/release-escrow", headers=bauth)
    assert release_res.status_code == 200
    released = release_res.json()
    assert released["status"] == "completed"

    seller_after = client.get(f"/api/v1/users/{seller_id}").json()
    assert seller_after["trust_score"] == 65
    buyer_after = client.get(f"/api/v1/users/{buyer_id}").json()
    assert buyer_after["trust_score"] == 55

    # 6. Buyer submits review (reviewer from JWT).
    review_res = client.post(
        "/api/v1/reviews/",
        headers=bauth,
        json={
            "order_id": order_id,
            "reviewer_id": buyer_id,
            "reviewee_id": seller_id,
            "rating": 5,
            "comment": "Book was in perfect condition!",
        },
    )
    assert review_res.status_code == 201

    seller_final = client.get(f"/api/v1/users/{seller_id}").json()
    assert seller_final["trust_score"] == 67
