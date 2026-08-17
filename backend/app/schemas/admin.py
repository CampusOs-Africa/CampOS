from typing import Any

from pydantic import BaseModel, Field


class StatusUpdate(BaseModel):
    is_active: bool


class RoleUpdate(BaseModel):
    role: str = Field(..., pattern=r"^(student|admin|verified_student|moderator)$")


class ListingModeration(BaseModel):
    reason: str | None = Field(None, max_length=500)


class AdminResponse(BaseModel):
    message: str
    data: Any | None = None
