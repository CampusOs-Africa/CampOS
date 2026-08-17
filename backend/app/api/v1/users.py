
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user_strict, hash_secret
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserProfileUpdate, UserResponse

router = APIRouter(prefix="/users", tags=["Users (Milestone 1 Integration)"])


class UserCreateRequest(BaseModel):
    name: str
    email: EmailStr
    password: str | None = Field(default=None, min_length=6)
    wallet_address: str | None = None
    # Legacy academic fields remain optional and default to None so that the
    # legacy endpoint no longer forces student data on registration.
    role: str = "student"
    school: str | None = None
    faculty: str | None = None
    department: str | None = None
    level: str | None = None


@router.post(
    "/",
    response_model=UserResponse,
    status_code=201,
    summary="Create a new user account (legacy)",
    description="Legacy endpoint. Prefer POST /api/v1/auth/register.",
)
def create_user(body: UserCreateRequest, db: Session = Depends(get_db)):
    repo = UserRepository(db)
    email = str(body.email).lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="User with this email already exists.")
    user = User(
        name=body.name,
        email=email,
        wallet_address=body.wallet_address,
        role="student",
        school=body.school,
        faculty=body.faculty,
        department=body.department,
        level=body.level,
        hashed_password=hash_secret(body.password) if body.password else None,
    )
    return repo.create(user)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the authenticated user's profile",
)
def get_my_profile(current_user: User = Depends(get_current_user_strict)):
    return current_user


# Profile fields used to calculate student-profile completeness (for UX only).
_PROFILE_FIELDS = (
    "name",
    "phone",
    "date_of_birth",
    "gender",
    "school",
    "faculty",
    "department",
    "level",
    "matric_number",
    "admission_year",
    "school_email",
)
_VERIFICATION_FIELDS = ("school_email",)


@router.get(
    "/me/completeness",
    summary="Profile completion indicator for the onboarding/selling flow",
)
def get_my_profile_completeness(current_user: User = Depends(get_current_user_strict)):
    filled = sum(
        1 for f in _PROFILE_FIELDS if getattr(current_user, f, None)
    )
    total = len(_PROFILE_FIELDS)
    pct = round(filled / total * 100)
    has_school_email = bool(current_user.school_email)
    is_verified = current_user.verification_status in ("verified", "approved")
    return {
        "completion_percent": pct,
        "filled_fields": filled,
        "total_fields": total,
        "missing_fields": [
            f for f in _PROFILE_FIELDS if not getattr(current_user, f, None)
        ],
        "has_school_email": has_school_email,
        "can_submit_verification": has_school_email,
        "is_verified": is_verified,
        "can_sell": is_verified,
    }


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update the authenticated user's profile",
    description=(
        "Updates profile/student fields. Identity is derived from the JWT; "
        "a user can only modify their own profile."
    ),
)
def update_my_profile(
    body: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_strict),
):
    data = body.model_dump(exclude_unset=True)

    # Email/wallet uniqueness checks when changing them.
    if data.get("school_email"):
        data["school_email"] = str(data["school_email"]).lower()
    if data.get("wallet_address"):
        existing = (
            db.query(User)
            .filter(
                User.wallet_address == data["wallet_address"],
                User.id != current_user.id,
            )
            .first()
        )
        if existing:
            raise HTTPException(status_code=409, detail="Wallet address already in use.")

    for field, value in data.items():
        setattr(current_user, field, value)

    repo = UserRepository(db)
    return repo.update(current_user)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
)
def get_user(user_id: str, db: Session = Depends(get_db)):
    user = UserRepository(db).get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


@router.get(
    "/",
    response_model=list[UserResponse],
    summary="List users",
)
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    db: Session = Depends(get_db),
):
    return UserRepository(db).get_all(skip=skip, limit=limit)
