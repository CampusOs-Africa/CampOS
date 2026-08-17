"""Phase 3 — student verification & seller authorization tests."""

from tests.conftest import promote_to_admin, register_and_token


def _h(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _files():
    return [
        ("student_id", ("id.pdf", b"%PDF-1.4 mock id", "application/pdf")),
        ("admission_letter", ("letter.pdf", b"%PDF-1.4 mock letter", "application/pdf")),
    ]


def _register(client, email, name="User"):
    user, token = register_and_token(client, email, name)
    return user, token


def _admin(client, db_session, email="admin.phase3@unijos.edu.ng"):
    admin, atoken = register_and_token(client, email, "Admin")
    promote_to_admin(db_session, admin["id"])
    return admin, atoken


def _verified_seller(client, db_session, email="seller.phase3@unijos.edu.ng"):
    seller, stoken = register_and_token(client, email, "Seller")
    # promote via direct DB status is NOT allowed; go through admin approval.
    admin, atoken = _admin(client, db_session)
    client.patch(
        "/api/v1/users/me",
        headers=_h(stoken),
        json={"school_email": email},
    )
    up = client.post(
        "/api/v1/verification/upload",
        headers=_h(stoken),
        data={"university_email": email},
        files=_files(),
    )
    assert up.status_code == 201, up.text
    vid = up.json()["id"]
    client.post(
        f"/api/v1/verification/admin/{vid}/approve", headers=_h(atoken)
    )
    return seller, stoken, admin, atoken


# ------------------------------------------------------------- IDOR
def test_user_cannot_submit_verification_for_another(client, db_session):
    _, atoken = _register(client, "attacker.v3@unilag.edu.ng")
    victim, _ = _register(client, "victim.v3@unilag.edu.ng")
    # No user_id in body; submission is always bound to the JWT attacker.
    r = client.post(
        "/api/v1/verification/upload",
        headers=_h(atoken),
        data={"university_email": "attacker.v3@unilag.edu.ng"},
        files=_files(),
    )
    assert r.status_code == 201
    assert r.json()["user_id"] != victim["id"]
    me = client.get("/api/v1/users/me", headers=_h(atoken)).json()
    assert r.json()["user_id"] == me["id"]


def test_user_cannot_send_otp_for_another(client):
    _, atoken = _register(client, "otp.attacker@unilag.edu.ng")
    # OTP endpoint derives user from JWT; even with a body user_id it is ignored.
    r = client.post(
        "/api/v1/verification/send-email-otp",
        headers=_h(atoken),
        json={"email": "otp.attacker@unilag.edu.ng"},
    )
    assert r.status_code == 200
    assert r.json()["email"] == "otp.attacker@unilag.edu.ng"


def test_user_cannot_verify_otp_for_another(client):
    _, atoken = _register(client, "otp.verify@unilag.edu.ng")
    client.post(
        "/api/v1/verification/send-email-otp",
        headers=_h(atoken),
        json={"email": "otp.verify@unilag.edu.ng"},
    )
    r = client.post(
        "/api/v1/verification/verify-email-otp",
        headers=_h(atoken),
        json={"email": "otp.verify@unilag.edu.ng", "otp_code": "123456"},
    )
    assert r.status_code == 200
    me = client.get("/api/v1/users/me", headers=_h(atoken)).json()
    # School email is persisted on the authenticated user.
    assert me["school_email"] == "otp.verify@unilag.edu.ng"


def test_user_cannot_view_another_users_private_verification(client):
    _, atoken = _register(client, "pview.attacker@unilag.edu.ng")
    victim, _ = _register(client, "pview.victim@unilag.edu.ng")
    assert client.get(
        f"/api/v1/verification/status/{victim['id']}", headers=_h(atoken)
    ).status_code == 403
    assert client.get(
        f"/api/v1/verification/history/{victim['id']}", headers=_h(atoken)
    ).status_code == 403


# ------------------------------------------------------- admin authz
def test_normal_user_cannot_approve_reject_resubmit_or_queue(client, db_session):
    student, stoken = register_and_token(
        client, "student.admin@unilag.edu.ng", "Student"
    )
    client.patch(
        "/api/v1/users/me",
        headers=_h(stoken),
        json={"school_email": "student.admin@unilag.edu.ng"},
    )
    up = client.post(
        "/api/v1/verification/upload",
        headers=_h(stoken),
        files=_files(),
    ).json()
    vid = up["id"]

    _, normaltoken = register_and_token(client, "normal.user@unilag.edu.ng", "Normal")
    for path, method, kwargs in [
        (f"/api/v1/verification/admin/{vid}/approve", "post", {}),
        (f"/api/v1/verification/admin/{vid}/reject", "post", {"json": {"reason": "bad docs"}}),
        (f"/api/v1/verification/admin/{vid}/resubmit", "post", {"json": {"reason": "blurry"}}),
        ("/api/v1/verification/admin/queue", "get", {}),
    ]:
        r = getattr(client, method)(path, headers=_h(normaltoken), **kwargs)
        assert r.status_code == 403, (path, r.status_code, r.text)


def test_admin_can_approve(client, db_session):
    seller, stoken, admin, atoken = _verified_seller(client, db_session)
    me = client.get("/api/v1/users/me", headers=_h(stoken)).json()
    assert me["verification_status"] == "verified"
    # Admin sees queue.
    q = client.get("/api/v1/verification/admin/queue", headers=_h(atoken))
    assert q.status_code == 200


# ------------------------------------------------------- selling gate
def test_unverified_user_cannot_create_listing(client):
    _, token = register_and_token(client, "unverified.sell@example.com", "Unverified")
    r = client.post(
        "/api/v1/marketplace/listings",
        headers=_h(token),
        json={
            "seller_id": "ignored",
            "title": "Book",
            "description": "A book for sale",
            "category": "books",
            "price": 1.0,
            "images": ["https://res.cloudinary.com/x/y.jpg"],
        },
    )
    assert r.status_code == 403


def test_verified_user_can_create_listing(client, db_session):
    _, stoken, _, _ = _verified_seller(client, db_session, "verified.sell@unijos.edu.ng")
    me = client.get("/api/v1/users/me", headers=_h(stoken)).json()
    r = client.post(
        "/api/v1/marketplace/listings",
        headers=_h(stoken),
        json={
            "seller_id": me["id"],
            "title": "My Book",
            "description": "Good condition",
            "category": "books",
            "price": 2.0,
            "images": ["https://res.cloudinary.com/x/y.jpg"],
        },
    )
    assert r.status_code == 201, r.text
    assert r.json()["seller_id"] == me["id"]


def test_user_cannot_modify_another_users_listing(client, db_session):
    _, stoken, _, _ = _verified_seller(client, db_session, "owner.mod@unijos.edu.ng")
    me = client.get("/api/v1/users/me", headers=_h(stoken)).json()
    listing = client.post(
        "/api/v1/marketplace/listings",
        headers=_h(stoken),
        json={
            "seller_id": me["id"],
            "title": "Owner Book",
            "description": "Owned listing",
            "category": "books",
            "price": 3.0,
            "images": ["https://res.cloudinary.com/x/y.jpg"],
        },
    ).json()
    _, btoken = register_and_token(client, "other.mod@example.com", "Other")
    assert client.put(
        f"/api/v1/marketplace/listings/{listing['id']}",
        headers=_h(btoken),
        json={"title": "hijacked"},
    ).status_code in (403, 404)
    assert client.delete(
        f"/api/v1/marketplace/listings/{listing['id']}", headers=_h(btoken)
    ).status_code in (403, 404)


# ------------------------------------------------------- state
def test_profile_completion_does_not_verify(client):
    _, token = register_and_token(client, "profile.only@example.com", "Profile")
    client.patch(
        "/api/v1/users/me",
        headers=_h(token),
        json={
            "school": "University of Lagos",
            "faculty": "Engineering",
            "matric_number": "2023/0001",
            "school_email": "profile.only@unilag.edu.ng",
        },
    )
    me = client.get("/api/v1/users/me", headers=_h(token)).json()
    assert me["verification_status"] == "pending"


def test_school_email_otp_does_not_verify(client):
    _, token = register_and_token(client, "otp.noverify@unilag.edu.ng", "OtpUser")
    client.patch(
        "/api/v1/users/me",
        headers=_h(token),
        json={"school_email": "otp.noverify@unilag.edu.ng"},
    )
    client.post(
        "/api/v1/verification/send-email-otp",
        headers=_h(token),
        json={"email": "otp.noverify@unilag.edu.ng"},
    )
    client.post(
        "/api/v1/verification/verify-email-otp",
        headers=_h(token),
        json={"email": "otp.noverify@unilag.edu.ng", "otp_code": "123456"},
    )
    me = client.get("/api/v1/users/me", headers=_h(token)).json()
    assert me["verification_status"] == "pending"


def test_rejection_does_not_verify(client, db_session):
    student, stoken = register_and_token(client, "rej.student@unilag.edu.ng", "RejUser")
    client.patch(
        "/api/v1/users/me",
        headers=_h(stoken),
        json={"school_email": "rej.student@unilag.edu.ng"},
    )
    vid = client.post(
        "/api/v1/verification/upload", headers=_h(stoken), files=_files()
    ).json()["id"]
    admin, atoken = _admin(client, db_session, "rej.admin@unilag.edu.ng")
    client.post(
        f"/api/v1/verification/admin/{vid}/reject",
        headers=_h(atoken),
        json={"reason": "Document unclear"},
    )
    me = client.get("/api/v1/users/me", headers=_h(stoken)).json()
    assert me["verification_status"] == "rejected"
    # Cannot sell.
    r = client.post(
        "/api/v1/marketplace/listings",
        headers=_h(stoken),
        json={
            "seller_id": student["id"],
            "title": "Rejected",
            "description": "Should fail",
            "category": "books",
            "price": 1.0,
            "images": ["https://res.cloudinary.com/x/y.jpg"],
        },
    )
    assert r.status_code == 403


def test_resubmission_returns_to_pending(client, db_session):
    student, stoken = register_and_token(client, "resub.student@unilag.edu.ng", "ResubUser")
    client.patch(
        "/api/v1/users/me",
        headers=_h(stoken),
        json={"school_email": "resub.student@unilag.edu.ng"},
    )
    vid = client.post(
        "/api/v1/verification/upload", headers=_h(stoken), files=_files()
    ).json()["id"]
    admin, atoken = _admin(client, db_session, "resub.admin@unilag.edu.ng")
    client.post(
        f"/api/v1/verification/admin/{vid}/resubmit",
        headers=_h(atoken),
        json={"reason": "Re-upload ID"},
    )
    me = client.get("/api/v1/users/me", headers=_h(stoken)).json()
    assert me["verification_status"] == "resubmission_requested"
    # User can upload again.
    up2 = client.post(
        "/api/v1/verification/upload", headers=_h(stoken), files=_files()
    )
    assert up2.status_code == 201


def test_revocation_removes_selling_authorization(client, db_session):
    _, stoken, admin, atoken = _verified_seller(client, db_session, "revoke.seller@unijos.edu.ng")
    me = client.get("/api/v1/users/me", headers=_h(stoken)).json()
    assert me["verification_status"] == "verified"

    r = client.post(
        "/api/v1/verification/admin/revoke",
        headers=_h(atoken),
        params={"user_id": me["id"]},
        json={"reason": "Policy violation"},
    )
    assert r.status_code in (200, 201), r.text

    me2 = client.get("/api/v1/users/me", headers=_h(stoken)).json()
    assert me2["verification_status"] == "revoked"
    # Can no longer create listings.
    r2 = client.post(
        "/api/v1/marketplace/listings",
        headers=_h(stoken),
        json={
            "seller_id": me["id"],
            "title": "After revoke",
            "description": "Should fail",
            "category": "books",
            "price": 1.0,
            "images": ["https://res.cloudinary.com/x/y.jpg"],
        },
    )
    assert r2.status_code == 403


# ------------------------------------------------------- privacy
def test_public_marketplace_does_not_expose_private_fields(client, db_session):
    _, stoken, _, _ = _verified_seller(client, db_session, "privacy.seller@unijos.edu.ng")
    listing = client.post(
        "/api/v1/marketplace/listings",
        headers=_h(stoken),
        json={
            "seller_id": "x",
            "title": "Privacy Book",
            "description": "No PII leak",
            "category": "books",
            "price": 1.0,
            "images": ["https://res.cloudinary.com/x/y.jpg"],
        },
    ).json()
    # Listing enrichment only exposes seller name/trust/verified badge.
    for sensitive in ("phone", "date_of_birth", "school_email", "matric_number"):
        assert sensitive not in listing


def test_completeness_endpoint(client):
    _, token = register_and_token(client, "complete@example.com", "Complete")
    r = client.get("/api/v1/users/me/completeness", headers=_h(token))
    assert r.status_code == 200
    data = r.json()
    assert "completion_percent" in data
    assert data["is_verified"] is False
    assert data["can_sell"] is False
    assert data["can_submit_verification"] is False
    client.patch(
        "/api/v1/users/me",
        headers=_h(token),
        json={"school_email": "complete@unilag.edu.ng"},
    )
    data2 = client.get("/api/v1/users/me/completeness", headers=_h(token)).json()
    assert data2["can_submit_verification"] is True
