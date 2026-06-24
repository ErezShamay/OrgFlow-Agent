from pydantic import BaseModel, Field

from app.auth.roles import (
    ORG_SCOPED_INVITE_ROLES,
    PLATFORM_INVITE_ROLES,
)
from app.schemas.email_fields import ValidatedEmail

ALLOWED_USER_ROLES = PLATFORM_INVITE_ROLES
ORG_ADMIN_INVITE_ROLES = ORG_SCOPED_INVITE_ROLES


class UserInviteRequest(BaseModel):
    email: ValidatedEmail
    full_name: str = Field(..., min_length=1, max_length=120)
    role: str = Field(default="VIEWER")
    organization_id: str | None = None


class ManagedUser(BaseModel):
    id: str
    email: str
    full_name: str | None = None
    role: str
    created_at: str | None = None


class UserUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, max_length=120)
    role: str | None = None
    organization_id: str | None = None


class UserSetPasswordRequest(BaseModel):
    password: str = Field(..., min_length=8, max_length=128)
    organization_id: str | None = None


ALL_ORGANIZATIONS_SCOPE = "__all__"
