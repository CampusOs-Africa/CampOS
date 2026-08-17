"""Phase 4 — admin dashboard, moderation & trust operations."""

from tests.conftest import promote_to_admin, register_and_token


def _h(token):
    return {"Authorization": f"Bearer {token}"}


def _admin(client, db_session, email="admin.p4@unijos.edu.ng"):
    admin, token = register_and_token(client, email, "Admin")
    promote_to_admin(db_session, admin["id"])
    return admin, token


def _student(client, email):
    return register_and_token(client, email, "Student")


# ------------------------------------------------------------- authorization
def test_admin_endpoints_require_auth(client):
    assert client.get("/api/v1/admin/dashboard").status_code == 401
    assert client.get("/api/v1/admin/users").status_code == 401


def test_normal_user_forbidden_from_admin(client, db_session):
    _, token = _student(client, "normal.p4@example.com")
    assert client.get("/api/v1/admin/dashboard", headers=_h(token)).status_code == 403
    assert client.get("/api/v1/admin/users", headers=_h(token)).status_code == 403
    assert client.get("/api/v1/admin/fraud", headers=_h(token)).status_code == 403
    assert client.get("/api/v1/admin/reviews", headers=_h(token)).status_code == 403
    assert client.get("/api/v1/admin/orders", headers=_h(token)).status_code == 403
    assert client.get("/api/v1/admin/listings", headers=_h(token)).status_code == 403


def test_admin_can_access_dashboard(client, db_session):
    _, token = _admin(client, db_session)
    r = client.get("/api/v1/admin/dashboard", headers=_h(token))
    assert r.status_code == 200, r.text
    data = r.json()
    assert "counts" in data
    assert "recent" in data
    # No password hashes leak.
    blob = r.text.lower()
    assert "hashed_password" not in blob
    assert "password" not in blob or "payment_reference" in blob


def test_forged_admin_id_is_ignored(client, db_session):
    # A normal user passing ?admin_id= must never become admin.
    _, token = _student(client, "forged.p4@example.com")
    r = client.get(
        "/api/v1/admin/dashboard?admin_id=someone", headers=_h(token)
    )
    assert r.status_code == 403


# ------------------------------------------------------------------- users
def test_admin_user_list_and_role_change(client, db_session):
    _, atoken = _admin(client, db_session, "role.admin@unijos.edu.ng")
    student, _ = _student(client, "role.target@example.com")

    listing = client.get("/api/v1/admin/users", headers=_h(atoken))
    assert listing.status_code == 200
    assert any(u["id"] == student["id"] for u in listing.json())

    r = client.patch(
        f"/api/v1/admin/users/{student['id']}/role",
        headers=_h(atoken),
        json={"role": "moderator"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["role"] == "moderator"


def test_normal_user_cannot_change_roles(client, db_session):
    _, atoken = _admin(client, db_session, "guard.admin@unijos.edu.ng")
    victim, _ = _student(client, "victim.role@example.com")
    attacker, btoken = _student(client, "attacker.role@example.com")
    # Attacker cannot promote themselves.
    r = client.patch(
        f"/api/v1/admin/users/{attacker['id']}/role",
        headers=_h(btoken),
        json={"role": "admin"},
    )
    assert r.status_code == 403


def test_cannot_demote_last_admin(client, db_session):
    admin, atoken = _admin(client, db_session, "last.admin@unijos.edu.ng")
    r = client.patch(
        f"/api/v1/admin/users/{admin['id']}/role",
        headers=_h(atoken),
        json={"role": "student"},
    )
    assert r.status_code == 403


def test_admin_can_deactivate_user(client, db_session):
    _, atoken = _admin(client, db_session, "deact.admin@unijos.edu.ng")
    user, _ = _student(client, "deact.target@example.com")
    r = client.patch(
        f"/api/v1/admin/users/{user['id']}/status",
        headers=_h(atoken),
        json={"is_active": False},
    )
    assert r.status_code == 200
    assert r.json()["is_active"] is False


# ----------------------------------------------------------- verifications
def test_admin_verification_moderation(client, db_session):
    _, atoken = _admin(client, db_session, "verif.admin@unijos.edu.ng")
    student, stoken = _student(client, "verif.student@unilag.edu.ng")
    client.patch(
        "/api/v1/users/me",
        headers=_h(stoken),
        json={"school_email": "verif.student@unilag.edu.ng"},
    )
    files = [
        ("student_id", ("id.pdf", b"%PDF-1.4 mock id", "application/pdf")),
        ("admission_letter", ("l.pdf", b"%PDF-1.4 mock letter", "application/pdf")),
    ]
    vid = client.post(
        "/api/v1/verification/upload", headers=_h(stoken), files=files
    ).json()["id"]

    # Approve via admin router.
    r = client.post(
        f"/api/v1/admin/verifications/{vid}/approve", headers=_h(atoken)
    )
    assert r.status_code == 200
    me = client.get("/api/v1/users/me", headers=_h(stoken)).json()
    assert me["verification_status"] == "verified"

    # Revoke
    r = client.post(
        "/api/v1/admin/verifications/revoke",
        headers=_h(atoken),
        params={"user_id": student["id"]},
        json={"reason": "policy"},
    )
    assert r.status_code in (200, 201)
    me = client.get("/api/v1/users/me", headers=_h(stoken)).json()
    assert me["verification_status"] == "revoked"


def test_normal_user_cannot_admin_verifications(client, db_session):
    _, atoken = _admin(client, db_session, "guard2.admin@unijos.edu.ng")
    student, stoken = _student(client, "verif2.student@unilag.edu.ng")
    client.patch(
        "/api/v1/users/me",
        headers=_h(stoken),
        json={"school_email": "verif2.student@unilag.edu.ng"},
    )
    files = [
        ("student_id", ("id.pdf", b"%PDF-1.4 mock id", "application/pdf")),
        ("admission_letter", ("l.pdf", b"%PDF-1.4 mock letter", "application/pdf")),
    ]
    vid = client.post(
        "/api/v1/verification/upload", headers=_h(stoken), files=files
    ).json()["id"]
    assert client.post(
        f"/api/v1/admin/verifications/{vid}/approve", headers=_h(stoken)
    ).status_code == 403
    assert client.get(
        "/api/v1/admin/verifications", headers=_h(stoken)
    ).status_code == 403


# -------------------------------------------------------------------- fraud
def test_admin_fraud_queue_and_resolve(client, db_session):
    _, atoken = _admin(client, db_session, "fraud.admin@unijos.edu.ng")
    reporter, rtoken = _student(client, "fraud.reporter@example.com")
    target, _ = _student(client, "fraud.target@example.com")
    rep = client.post(
        "/api/v1/fraud/reports",
        headers=_h(rtoken),
        json={
            "reporter_id": reporter["id"],
            "reported_user_id": target["id"],
            "category": "other",
            "description": "Suspicious behavior described here.",
        },
    ).json()
    assert client.get("/api/v1/admin/fraud", headers=_h(atoken)).status_code == 200
    r = client.post(
        f"/api/v1/admin/fraud/{rep['id']}/resolve",
        headers=_h(atoken),
        json={"status": "resolved_dismissed", "resolution_notes": "No evidence"},
    )
    assert r.status_code == 200, r.text


def test_normal_user_cannot_access_fraud_admin(client, db_session):
    _, token = _student(client, "fraud.normal@example.com")
    assert client.get("/api/v1/admin/fraud", headers=_h(token)).status_code == 403


# ------------------------------------------------------------------ reviews
def test_admin_review_moderation(client, db_session):
    _, atoken = _admin(client, db_session, "reviews.admin@unijos.edu.ng")
    # A flagged review can be moderated. Create via service path is complex;
    # ensure endpoint enforces admin and returns the queue.
    r = client.get("/api/v1/admin/reviews", headers=_h(atoken))
    assert r.status_code == 200
    assert client.get("/api/v1/admin/reviews").status_code == 401


# ---------------------------------------------------------------- listings
def test_admin_suspend_and_restore_listing(client, db_session):
    from tests.test_phase3_verification import _verified_seller, _files  # noqa

    _, stoken, _, _ = _verified_seller(client, db_session, "mod.seller@unijos.edu.ng")
    me = client.get("/api/v1/users/me", headers=_h(stoken)).json()
    listing = client.post(
        "/api/v1/marketplace/listings",
        headers=_h(stoken),
        json={
            "seller_id": me["id"],
            "title": "Suspend Me",
            "description": "To be suspended",
            "category": "books",
            "price": 1.0,
            "images": ["https://res.cloudinary.com/x/y.jpg"],
        },
    ).json()
    # The route overwrites seller_id with the JWT; fetch actual seller id.
    me = client.get("/api/v1/users/me", headers=_h(stoken)).json()

    _, atoken = _admin(client, db_session, "listing.admin@unijos.edu.ng")
    r = client.post(
        f"/api/v1/admin/listings/{listing['id']}/suspend",
        headers=_h(atoken),
        json={"reason": "prohibited item"},
    )
    assert r.status_code == 200, r.text
    # Suspended listing hidden from public catalog.
    catalog = client.get("/api/v1/marketplace/listings").json()
    assert all(x["id"] != listing["id"] for x in catalog)

    # Restoring works because seller remains verified.
    r = client.post(
        f"/api/v1/admin/listings/{listing['id']}/restore",
        headers=_h(atoken),
        json={},
    )
    assert r.status_code == 200, r.text


def test_normal_user_cannot_moderate_listings(client, db_session):
    _, atoken = _admin(client, db_session, "guard3.admin@unijos.edu.ng")
    other_user, other_token = _student(client, "mod.other@example.com")
    assert client.post(
        "/api/v1/admin/listings/whatever/suspend",
        headers=_h(other_token),
        json={},
    ).status_code == 403


# ------------------------------------------------------------------- orders
def test_admin_order_overview(client, db_session):
    _, atoken = _admin(client, db_session, "orders.admin@unijos.edu.ng")
    assert client.get("/api/v1/admin/orders", headers=_h(atoken)).status_code == 200


def test_audit_log_records_actions(client, db_session):
    _, atoken = _admin(client, db_session, "audit.admin@unijos.edu.ng")
    user, _ = _student(client, "audit.target@example.com")
    client.patch(
        f"/api/v1/admin/users/{user['id']}/role",
        headers=_h(atoken),
        json={"role": "moderator"},
    )
    logs = client.get("/api/v1/admin/audit", headers=_h(atoken)).json()
    assert any(entry["action"] == "user.role_change" for entry in logs)
