import hashlib
import hmac
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from fastapi import Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import CampusOSException, ForbiddenError
from app.models.user import User
from app.repositories.user_repository import UserRepository


def utc_now():
    return datetime.now(UTC)


def create_access_token(
    subject: str,
    role: str = "student",
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed HMAC-SHA256 JWT access token."""
    if expires_delta:
        expire = utc_now() + expires_delta
    else:
        expire = utc_now() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": subject,
        "role": role,
        "iat": int(utc_now().timestamp()),
        "exp": int(expire.timestamp()),
        "iss": "CampusOS-Auth-Engine",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def verify_access_token(token: str) -> dict[str, Any]:
    """Verify and decode a signed HMAC-SHA256 JWT access token with multi-key rotation support."""
    keys = settings.get_jwt_secret_keys()
    last_err = None
    for key in keys:
        try:
            payload = jwt.decode(
                token,
                key,
                algorithms=[settings.JWT_ALGORITHM],
                issuer="CampusOS-Auth-Engine",
            )
            return payload
        except jwt.ExpiredSignatureError as e:
            raise CampusOSException(
                "JWT access token has expired. Please log in again.",
                code="TOKEN_EXPIRED",
                status_code=401,
            ) from e
        except jwt.InvalidTokenError as e:
            last_err = e
            continue

    raise CampusOSException(
        "Invalid JWT access token cryptographic signature.",
        code="INVALID_TOKEN",
        status_code=401,
    ) from last_err


def hash_secret(secret: str, salt: str = "campusos-salt") -> str:
    """Compute PBKDF2 HMAC-SHA256 hash for password or secret storage."""
    return hashlib.pbkdf2_hmac(
        "sha256",
        secret.encode("utf-8"),
        salt.encode("utf-8"),
        100000,
    ).hex()


def verify_secret(secret: str, hashed_secret: str, salt: str = "campusos-salt") -> bool:
    """Constant-time comparison of a plaintext secret against its PBKDF2 hash."""
    computed_hash = hash_secret(secret, salt)
    return hmac.compare_digest(computed_hash, hashed_secret)


def check_role_permission(user_role: str, required_roles: list[str]) -> None:
    """Check if the user's role is authorized in the required roles list."""
    if user_role not in required_roles:
        raise ForbiddenError(
            f"Access denied. Required role(s): {required_roles}; Current role: '{user_role}'."
        )


# HTTP Bearer token extraction.
optional_bearer = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_bearer),
    db: Session = Depends(get_db),
) -> User | None:
    """Resolve the current user from a Bearer JWT, or None if absent."""
    if credentials and credentials.credentials:
        payload = verify_access_token(credentials.credentials)
        user = UserRepository(db).get_by_id(payload.get("sub") or "")
        if not user:
            raise CampusOSException(
                "Invalid or expired authentication token.",
                code="INVALID_TOKEN",
                status_code=401,
            )
        return user
    return None


async def get_current_user(
    user: User | None = Depends(get_current_user_optional),
) -> User:
    """Require an authenticated user (via JWT or explicit demo identifier)."""
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="This account has been suspended.")
    return user


async def get_current_user_strict(
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Require a valid JWT with NO demo fallback.

    Use this for any state-changing/authenticated action where client-supplied
    identifiers must not be trusted.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Authentication required.")
    payload = verify_access_token(credentials.credentials)
    user = UserRepository(db).get_by_id(payload.get("sub") or "")
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="This account has been suspended.")
    return user


async def require_admin(user: User = Depends(get_current_user_strict)) -> User:
    """Require an authenticated administrator (JWT only, no demo fallback)."""
    if user.role != "admin":
        raise ForbiddenError("Only administrators can perform this action.")
    return user
