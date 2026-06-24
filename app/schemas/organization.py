from pydantic import BaseModel, Field

from app.schemas.email_fields import ValidatedEmail


class OrganizationCreateRequest(BaseModel):
    organization_name: str = Field(..., min_length=1, max_length=200)
    contact_email: ValidatedEmail
