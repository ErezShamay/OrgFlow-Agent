from __future__ import annotations

from app.exceptions.exceptions import (
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.repositories.organization_repository import (
    OrganizationRepository,
)
from app.repositories.tenant_manager_module_repository import (
    TenantManagerModuleRepository,
)


class TenantManagerModuleService:
    def __init__(
        self,
        module_repository:
            TenantManagerModuleRepository | None = None,
        organization_repository:
            OrganizationRepository | None = None,
    ) -> None:
        self.module_repository = (
            module_repository or TenantManagerModuleRepository()
        )
        self.organization_repository = (
            organization_repository or OrganizationRepository()
        )

    def is_storage_available(self) -> bool:
        return self.module_repository.is_storage_available()

    def is_enabled_for_organization(
        self,
        organization_id: str,
    ) -> bool:
        record = self.module_repository.get_by_organization_id(
            organization_id
        )
        return bool(record and record.get("is_enabled"))

    def get_status(
        self,
        organization_id: str,
    ) -> dict:
        record = self.module_repository.get_by_organization_id(
            organization_id
        )

        return {
            "organization_id": organization_id,
            "is_enabled": bool(record and record.get("is_enabled")),
            "enabled_at": record.get("enabled_at") if record else None,
            "disabled_at": record.get("disabled_at") if record else None,
            "enabled_by_profile_id": (
                record.get("enabled_by_profile_id") if record else None
            ),
            "storage_available": self.is_storage_available(),
        }

    def list_all_with_organizations(
        self,
    ) -> dict:
        organizations = (
            self.organization_repository.get_all_organizations()
        )
        module_by_org = {
            str(item["organization_id"]): item
            for item in self.module_repository.list_all()
        }

        items = []

        for organization in organizations:
            org_id = str(organization["id"])
            module = module_by_org.get(org_id)
            items.append({
                "organization_id": org_id,
                "organization_name": (
                    organization.get("organization_name")
                    or organization.get("name")
                    or org_id
                ),
                "contact_email": organization.get("contact_email"),
                "is_enabled": bool(
                    module and module.get("is_enabled")
                ),
                "enabled_at": module.get("enabled_at") if module else None,
                "disabled_at": (
                    module.get("disabled_at") if module else None
                ),
                "enabled_by_profile_id": (
                    module.get("enabled_by_profile_id")
                    if module
                    else None
                ),
            })

        return {
            "organizations": items,
            "total": len(items),
            "storage_available": self.is_storage_available(),
        }

    def set_enabled(
        self,
        *,
        organization_id: str,
        is_enabled: bool,
        actor_profile_id: str,
    ) -> dict:
        organization = self.organization_repository.get_by_id(
            organization_id
        )

        if not organization:
            raise NotFoundError(
                message="Organization not found",
                resource_type="organization",
                resource_id=organization_id,
            )

        if not self.is_storage_available():
            raise ValidationError(
                message=(
                    "מודול מנהל דיירים אינו מוגדר במסד הנתונים. "
                    "יש להריץ את המיגרציה "
                    "db/migrations/2026061101_organization_tenant_manager_module.sql"
                ),
            )

        record = self.module_repository.upsert_status(
            organization_id=organization_id,
            is_enabled=is_enabled,
            enabled_by_profile_id=(
                actor_profile_id if is_enabled else None
            ),
        )

        return self._serialize_record(record)

    def require_enabled(
        self,
        organization_id: str,
    ) -> None:
        if not self.is_enabled_for_organization(organization_id):
            raise ForbiddenError(
                "מודול מנהל דיירים אינו מופעל עבור ארגון זה"
            )

    @staticmethod
    def _serialize_record(record: dict) -> dict:
        return {
            "organization_id": str(record["organization_id"]),
            "is_enabled": bool(record.get("is_enabled")),
            "enabled_at": record.get("enabled_at"),
            "disabled_at": record.get("disabled_at"),
            "enabled_by_profile_id": record.get(
                "enabled_by_profile_id"
            ),
            "storage_available": True,
        }
