"""Phase 2 — profile completion & onboarding tests."""

from fastapi.testclient import TestClient

from tests.conftest import register_and_token



def _register(client: TestClient, email: str = "student@example.com", name: str = "Student"):
    r = client.post(
        "/api/v1/auth/register",
        json={"name": name, "email": email, "password": "CampusOS2026!"},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    return body["user"], body["access_token"]


def _h(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------- registration
def test_register_accepts_any_email_and_no_academic_info(client):
    user, token = _register(client, "anyone@gmail.com")
    assert user["email"] == "anyone@gmail.com"
    # No academic information required at signup.
    for field in ("school", "faculty", "department", "level", "matric_number"):
        assert user.get(field) is None
    me = client.get("/api/v1/users/me", headers=_h(token)).json()
    assert me["email"] == "anyone@gmail.com"
    assert me["verification_status"] == "pending"


def test_password_login_works(client):
    _register(client, "loginme@gmail.com")
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "loginme@gmail.com", "password": "CampusOS2026!"},
    )
    assert r.status_code == 200
    assert r.json()["access_token"]


def test_school_email_not_required_at_signup(client):
    # Registration with a plain email succeeds; no .edu required.
    user, _ = _register(client, "plainemail@yahoo.com")
    assert user["school_email"] is None


# ---------------------------------------------------------------- profile
def test_user_can_get_and_update_own_profile(client):
    user, token = _register(client, "profile@gmail.com")
    payload = {
        "phone": "+234 803 000 1234",
        "date_of_birth": "2004-05-15",
        "gender": "Female",
        "school": "University of Lagos",
        "faculty": "Engineering",
        "department": "Electrical Engineering",
        "level": "300 Level",
        "matric_number": "2023/240182",
        "admission_year": "2023",
        "school_email": "profile@unilag.edu.ng",
    }
    r = client.patch("/api/v1/users/me", headers=_h(token), json=payload)
    assert r.status_code == 200, r.text
    updated = r.json()
    assert updated["school"] == "University of Lagos"
    assert updated["matric_number"] == "2023/240182"
    assert updated["school_email"] == "profile@unilag.edu.ng"
    # hashed password must never be returned
    assert "hashed_password" not in updated


def test_profile_changes_persist_across_relogin(client):
    user, token = _register(client, "persist@gmail.com")
    client.patch(
        "/api/v1/users/me", headers=_h(token), json={"school": "Ahmadu Bello University"}
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "persist@gmail.com", "password": "CampusOS2026!"},
    ).json()
    me = client.get("/api/v1/users/me", headers=_h(login["access_token"])).json()
    assert me["school"] == "Ahmadu Bello University"


def test_user_cannot_modify_another_users_profile(client):
    _, token_a = _register(client, "a_persist@gmail.com", "Alice")
    _, token_b = _register(client, "b_persist@gmail.com", "Bob")
    r = client.patch(
        "/api/v1/users/me", headers=_h(token_b), json={"name": "Hijacked"}
    )
    assert r.status_code == 200
    # Alice's name is unchanged.
    me_a = client.get("/api/v1/users/me", headers=_h(token_a)).json()
    assert me_a["name"] == "Alice"


def test_empty_optional_student_fields_allowed(client):
    _, token = _register(client, "emptyfields@gmail.com")
    r = client.patch(
        "/api/v1/users/me",
        headers=_h(token),
        json={"school": None, "faculty": None, "matric_number": None},
    )
    assert r.status_code == 200
    assert r.json()["school"] is None


def test_profile_requires_auth(client):
    assert client.get("/api/v1/users/me").status_code == 401
    assert client.patch("/api/v1/users/me", json={"name": "x"}).status_code == 401


# ---------------------------------------------------------------- selling gate
def test_unverified_user_cannot_create_listing(client):
    _, token = _register(client, "cantsell@gmail.com")
    r = client.post(
        "/api/v1/marketplace/listings",
        headers=_h(token),
        json={
            "seller_id": "ignored",
            "title": "Book",
            "description": "A textbook for sale",
            "category": "books",
            "price": 5.0,
            "images": ["https://res.cloudinary.com/x/y.jpg"],
        },
    )
    assert r.status_code == 403


def test_normal_user_can_browse_and_buy(client, db_session):
    _, token = _register(client, "browser@gmail.com")
    # Browsing is public.
    assert client.get("/api/v1/marketplace/listings").status_code == 200
    # Buying: create a verified seller, listing, then buyer initiates checkout.
    from app.models.user import User

    seller, stoken = register_and_token(client, "seller_browse@unijos.edu.ng", "Seller")
    su = db_session.get(User, seller["id"])
    su.verification_status = "verified"
    db_session.commit()
    listing = client.post(
        "/api/v1/marketplace/listings",
        headers=_h(stoken),
        json={
            "seller_id": seller["id"],
            "title": "Readable Book",
            "description": "Good condition book",
            "category": "books",
            "price": 3.0,
            "images": ["https://res.cloudinary.com/x/y.jpg"],
        },
    ).json()
    buy = client.post(
        "/api/v1/payments/initiate",
        headers=_h(token),
        json={"buyer_id": "ignored", "listing_id": listing["id"], "amount": 3.0},
    )
    assert buy.status_code == 201
    assert buy.json()["order_id"]


# ---------------------------------------------------------------- verification
def test_filling_profile_does_not_auto_verify(client):
    user, token = _register(client, "notverified@gmail.com")
    client.patch(
        "/api/v1/users/me",
        headers=_h(token),
        json={
            "school": "University of Lagos",
            "matric_number": "2023/0001",
            "school_email": "notverified@unilag.edu.ng",
        },
    )
    me = client.get("/api/v1/users/me", headers=_h(token)).json()
    assert me["verification_status"] == "pending"


def test_verification_uses_profile_school_email(client, db_session):
    from app.models.user import User

    user, token = _register(client, "verifprofile@unilag.edu.ng", "Verif")
    # Set school email on profile.
    client.patch(
        "/api/v1/users/me",
        headers=_h(token),
        json={"school_email": "verifprofile@unilag.edu.ng"},
    )
    # Upload without explicitly passing university_email -> uses profile email.
    files = [
        ("student_id", ("id.pdf", b"%PDF-1.4 mock", "application/pdf")),
        ("admission_letter", ("letter.pdf", b"%PDF-1.4 mock", "application/pdf")),
    ]
    r = client.post("/api/v1/verification/upload", headers=_h(token), files=files)
    assert r.status_code == 201, r.text
    assert r.json()["university_email"] == "verifprofile@unilag.edu.ng"


def test_user_cannot_submit_verification_for_another(client, db_session):
    _, token_attacker = _register(client, "attacker.verif@unilag.edu.ng", "Attacker")
    victim, _ = _register(client, "victim.verif@unilag.edu.ng", "Victim")
    files = [
        ("student_id", ("id.pdf", b"%PDF-1.4 mock", "application/pdf")),
        ("admission_letter", ("letter.pdf", b"%PDF-1.4 mock", "application/pdf")),
    ]
    # Submission is always bound to the JWT user, never to a client-supplied id.
    r = client.post(
        "/api/v1/verification/upload",
        headers=_h(token_attacker),
        data={"university_email": "attacker.verif@unilag.edu.ng"},
        files=files,
    )
    assert r.status_code == 201, r.text
    assert r.json()["user_id"] != victim["id"]
    me = client.get("/api/v1/users/me", headers=_h(token_attacker)).json()
    assert r.json()["user_id"] == me["id"]


def test_admin_approval_makes_user_eligible_to_sell(client, db_session):
    from app.models.user import User

    user, token = _register(client, "approved.seller@unijos.edu.ng", "Approved")
    client.patch(
        "/api/v1/users/me",
        headers=_h(token),
        json={"school_email": "approved.seller@unijos.edu.ng"},
    )
    files = [
        ("student_id", ("id.pdf", b"%PDF-1.4 mock", "application/pdf")),
        ("admission_letter", ("letter.pdf", b"%PDF-1.4 mock", "application/pdf")),
    ]
    verif = client.post(
        "/api/v1/verification/upload", headers=_h(token), files=files
    ).json()

    admin, atoken = register_and_token(client, "admin.approve@unijos.edu.ng", "Admin")
    db_session.get(User, admin["id"]).role = "admin"
    db_session.commit()
    approve = client.post(
        f"/api/v1/verification/admin/{verif['id']}/approve",
        headers={"Authorization": f"Bearer {atoken}"},
    )
    assert approve.status_code == 200
    me = client.get("/api/v1/users/me", headers=_h(token)).json()
    assert me["verification_status"] == "verified"

    # Now the user can sell.
    r = client.post(
        "/api/v1/marketplace/listings",
        headers=_h(token),
        json={
            "seller_id": user["id"],
            "title": "After Approval",
            "description": "Can sell now",
            "category": "books",
            "price": 2.0,
            "images": ["https://res.cloudinary.com/x/y.jpg"],
        },
    )
    assert r.status_code == 201
