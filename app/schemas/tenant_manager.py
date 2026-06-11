from datetime import datetime

from pydantic import BaseModel


class TenantManagerModuleStatus(BaseModel):
    organization_id: str
    is_enabled: bool
    enabled_at: datetime | None = None
    disabled_at: datetime | None = None
    enabled_by_profile_id: str | None = None
    storage_available: bool = True


class TenantManagerModuleToggleRequest(BaseModel):
    is_enabled: bool
