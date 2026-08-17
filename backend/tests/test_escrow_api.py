from tests.conftest import promote_to_admin, register_and_token


def test_escrow_api_endpoints(client, db_session):
    seller, stoken = register_and_token(
        client, "amina.escrowapi@unijos.edu.ng", "Amina Bello"
    )
    sauth = {"Authorization": f"Bearer {stoken}"}
    buyer, btoken = register_and_token(
        client, "chidi.escrowapi@unijos.edu.ng", "Chidi Okafor"
    )
    bauth = {"Authorization": f"Bearer {btoken}"}
    admin, atoken = register_and_token(
        client, "admin.escrowapi@unijos.edu.ng", "Admin User"
    )
    promote_to_admin(db_session, admin["id"])
    aauth = {"Authorization": f"Bearer {atoken}"}

    # Approve seller verification.
    verif = client.post(
        "/api/v1/verification/upload",
        headers=sauth,
        data={"university_email": "amina.escrowapi@unijos.edu.ng"},
        files=[
            ("student_id", ("id.pdf", b"%PDF-1.4 mock id", "application/pdf")),
            ("admission_letter", ("letter.pdf", b"%PDF-1.4 mock letter", "application/pdf")),
        ],
    ).json()
    client.post(f"/api/v1/verification/admin/{verif['id']}/approve", headers=aauth)

    # Seller creates a listing.
    listing = client.post(
        "/api/v1/marketplace/listings",
        headers=sauth,
        json={
            "seller_id": seller["id"],
            "title": "Calculus Notes",
            "description": "Clean engineering notes",
            "category": "books",
            "price": 3000.0,
            "images": ["https://res.cloudinary.com/notes.jpg"],
        },
    ).json()

    # Buyer creates the order (buyer is derived from JWT).
    order = client.post(
        "/api/v1/orders/",
        headers=bauth,
        json={"buyer_id": buyer["id"], "listing_id": listing["id"], "amount": 3000.0},
    ).json()

    # Buyer creates escrow (buyer forced from JWT).
    create_res = client.post(
        "/api/v1/escrow/create",
        headers=bauth,
        json={
            "order_id": order["id"],
            "buyer_id": buyer["id"],
            "seller_id": seller["id"],
            "amount": 3000.0,
        },
    )
    assert create_res.status_code == 201
    escrow = create_res.json()
    assert escrow["state"] == "CREATED"
    assert escrow["order_id"] == order["id"]

    # Participants can read the escrow.
    get_res = client.get(f"/api/v1/escrow/{escrow['id']}", headers=bauth)
    assert get_res.status_code == 200
    assert get_res.json()["quai_order_id"] == escrow["quai_order_id"]

    # Buyer disputes.
    dispute_res = client.post(
        "/api/v1/escrow/dispute",
        headers=bauth,
        json={"order_id": order["id"], "actor_id": buyer["id"], "reason": "Item delayed"},
    )
    assert dispute_res.status_code == 200
    assert dispute_res.json()["state"] == "DISPUTED"

    # Buyer/admin releases after dispute resolution.
    release_res = client.post(
        "/api/v1/escrow/release",
        headers=bauth,
        json={"order_id": order["id"], "actor_id": buyer["id"]},
    )
    assert release_res.status_code == 200
    assert release_res.json()["state"] == "COMPLETED"
    assert release_res.json()["escrow_tx_hash"].startswith("0xquai_escrow_release_")
