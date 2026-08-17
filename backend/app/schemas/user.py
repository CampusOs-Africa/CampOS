from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    phone: str | None = None
    date_of_birth: str | None = None
    gender: str | None = None
    wallet_address: str | None = None
    student_id: str | None = None
    school: str | None = None
    faculty: str | None = None
    department: str | None = None
    level: str | None = None
    matric_number: str | None = None
    admission_year: str | None = None
    school_email: str | None = None
    trust_score: int
    verification_status: str
    role: str
    is_active: bool = True
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserProfileUpdate(BaseModel):
    """Editable profile fields. All optional; identity comes from the JWT."""

    name: str | None = Field(None, min_length=2, max_length=100)
    phone: str | None = Field(None, max_length=30)
    date_of_birth: str | None = Field(
        None, description="ISO date (YYYY-MM-DD)", pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    gender: str | None = Field(None, max_length=30)
    wallet_address: str | None = Field(None, max_length=100)
    student_id: str | None = Field(None, max_length=100)
    school: str | None = Field(None, max_length=150)
    faculty: str | None = Field(None, max_length=150)
    department: str | None = Field(None, max_length=150)
    level: str | None = Field(None, max_length=50)
    matric_number: str | None = Field(None, max_length=100)
    admission_year: str | None = Field(
        None, pattern=r"^\d{4}$", description="4-digit admission year"
    )
    school_email: EmailStr | None = None
