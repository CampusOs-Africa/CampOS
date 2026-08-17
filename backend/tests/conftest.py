import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 - Populate Base.metadata with all models
from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import hash_secret
from app.main import app as fastapi_app
from app.models.user import User

# Set environment to test so rate limiting middleware does not throttle pytest
settings.ENVIRONMENT = "test"

# Use in-memory SQLite database with StaticPool so all connections see the same tables
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

TEST_PASSWORD = "CampusOS2026!"


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    from app.core import rate_limit
    rate_limit._hits.clear()
    rate_limit._locks.clear()
    yield


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Authentication helpers (tests must authenticate via the real JWT flow).
# ---------------------------------------------------------------------------
def _register(client: TestClient, email: str, name: str = "Test User") -> dict:
    resp = client.post(
        "/api/v1/auth/register",
        json={"name": name, "email": email, "password": TEST_PASSWORD},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def make_user(client, db_session):
    """Create a verified-or-unverified user and return (user, token, headers)."""

    def _make(email: str, name: str = "Student", verified: bool = False, role: str = "student"):
        data = _register(client, email, name)
        user = data["user"]
        token = data["access_token"]
        # Promote role / verification directly in the DB when a test needs it.
        db_user = db_session.query(User).filter(User.id == user["id"]).first()
        if role != "student":
            db_user.role = role
        if verified:
            db_user.verification_status = "verified"
        db_session.commit()
        db_session.refresh(db_user)
        user = {**user, "role": db_user.role, "verification_status": db_user.verification_status}
        return user, token, auth_headers(token)

    return _make


@pytest.fixture
def admin(make_user):
    """Return (admin_user, token, headers) for an authenticated admin."""
    return make_user("admin.test@unijos.edu.ng", name="Test Admin", role="admin")


def register_and_token(client: TestClient, email: str, name: str = "User", password: str = TEST_PASSWORD):
    r = client.post(
        "/api/v1/auth/register",
        json={"name": name, "email": email, "password": password},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    return body["user"], body["access_token"]


def promote_to_admin(db_session, user_id: str):
    user = db_session.get(User, user_id)
    user.role = "admin"
    db_session.commit()


def make_user_verified(db_session, user_id: str):
    user = db_session.get(User, user_id)
    user.verification_status = "verified"
    db_session.commit()
