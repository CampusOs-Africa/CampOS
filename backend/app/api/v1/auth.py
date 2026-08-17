from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import auth_limiter
from app.core.security import (
    create_access_token,
    get_current_user_strict,
    hash_secret,
    verify_secret,
)
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new CampusOS account",
    description=(
        "Creates an account from any valid email address. No student/institutional "
        "email or verification is required at signup; verification is only required "
        "to become a seller."
    ),
)
def register(body: RegisterRequest, db: Session = Depends(get_db), _r=Depends(auth_limiter)) -> TokenResponse:
    email = str(body.email).lower()
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        name=body.name.strip(),
        email=email,
        hashed_password=hash_secret(body.password),
        role="student",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=user.id, role=user.role)
    return TokenResponse(
        access_token=token,
        expires_in=24 * 60 * 60,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in with email and password",
)
def login(body: LoginRequest, db: Session = Depends(get_db), _r=Depends(auth_limiter)) -> TokenResponse:
    email = str(body.email).lower()
    user = db.query(User).filter(User.email == email).first()

    # Constant-time behavior: always run a hash comparison even when the user
    # does not exist, to avoid leaking account existence via timing.
    stored = user.hashed_password if (user and user.hashed_password) else hash_secret("invalid")
    if not user or not user.hashed_password or not verify_secret(body.password, stored):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been suspended.",
        )

    token = create_access_token(subject=user.id, role=user.role)
    return TokenResponse(
        access_token=token,
        expires_in=24 * 60 * 60,
        user=UserResponse.model_validate(user),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the currently authenticated user",
)
def me(current_user: User = Depends(get_current_user_strict)) -> User:
    return current_user


@router.post(
    "/demo-login",
    response_model=TokenResponse,
    include_in_schema=False,
    summary="One-click demo login (development/demo only)",
)
def demo_login(body: dict, db: Session = Depends(get_db), _r=Depends(auth_limiter)) -> TokenResponse:
    """Mint a JWT for a seeded demo account (demo mode only).

    Disabled unless ALLOW_DEMO_LOGIN=true. Only resolves existing active
    users; it never creates accounts, never changes roles, and never bypasses
    authorization. This is a Builderthon/demo convenience, not real auth.
    """
    if not settings.ALLOW_DEMO_LOGIN:
        raise HTTPException(status_code=404, detail="Not found.")
    user_id = (body or {}).get("user_id")
    if not user_id or not isinstance(user_id, str):
        raise HTTPException(status_code=400, detail="Invalid request.")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=404, detail="Not found.")
    token = create_access_token(subject=user.id, role=user.role)
    return TokenResponse(
        access_token=token,
        expires_in=24 * 60 * 60,
        user=UserResponse.model_validate(user),
    )
