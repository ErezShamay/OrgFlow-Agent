from __future__ import annotations

import logging

from app.exceptions.exceptions import (
    ValidationError,
)
from app.lib.email_validation import require_valid_email
from app.repositories.organization_repository import (
    OrganizationRepository,
)
from app.auth.roles import is_platform_admin
from app.repositories.profile_repository import (
    ProfileRepository,
)
from app.exceptions.exceptions import ForbiddenError
from app.services.organization_deletion_service import (
    OrganizationDeletionService,
)
from app.services.tenant_access_service import (
    TenantAccessService,
)

logger = logging.getLogger(__name__)


class OrganizationAdminService:
    def __init__(
        self,
        organization_repository:
            OrganizationRepository | None = None,
        profile_repository: ProfileRepository | None = None,
        tenant_access_service: TenantAccessService | None = None,
        organization_deletion_service:
            OrganizationDeletionService | None = None,
    ) -> None:
        self.organization_repository = (
            organization_repository or OrganizationRepository()
        )
        self.profile_repository = (
            profile_repository or ProfileRepository()
        )
        self.tenant_access_service = (
            tenant_access_service or TenantAccessService()
        )
        self.organization_deletion_service = (
            organization_deletion_service
            or OrganizationDeletionService(
                organization_repository=self.organization_repository,
                profile_repository=self.profile_repository,
            )
        )

    def list_accessible_organizations(
        self,
        profile_id: str,
    ) -> dict:
        organizations = (
            self.tenant_access_service
            .list_accessible_organizations(profile_id)
        )
        organizations = (
            self.organization_repository
            .attach_projects(organizations)
        )

        return {
            "organizations": organizations,
            "total": len(organizations),
        }

    def create_customer_organization(
        self,
        *,
        organization_name: str,
        contact_email: str,
        owner_profile_id: str,
    ) -> dict:
        normalized_name = organization_name.strip()

        if not normalized_name:
            raise ValidationError(message="Organization name is required")

        try:
            normalized_email = require_valid_email(contact_email)
        except ValueError as error:
            raise ValidationError(message="Invalid contact email") from error

        organization = (
            self.organization_repository.create_organization(
                name=normalized_name,
                contact_email=normalized_email,
                owner_profile_id=owner_profile_id,
            )
        )

        org_id = str(organization["id"]).strip()
        profile = self.profile_repository.get_profile_by_id(
            owner_profile_id
        )

        if (
            profile
            and not is_platform_admin(profile.get("role"))
            and not ProfileRepository.extract_organization_id(profile)
        ):
            try:
                self.profile_repository.update_profile(
                    owner_profile_id,
                    {"organization_id": org_id},
                )
            except Exception as error:
                logger.warning(
                    "Could not assign owner profile to new organization",
                    extra={
                        "event": "audit.org_create_profile_link_failed",
                        "profile_id": owner_profile_id,
                        "organization_id": org_id,
                        "error": str(error),
                    },
                )

        logger.info(
            "Customer organization created",
            extra={
                "event": "audit.organization_create",
                "organization_id": org_id,
                "owner_profile_id": owner_profile_id,
            },
        )

        return {
            "organization": organization,
        }

    def delete_customer_organization(
        self,
        *,
        organization_id: str,
        actor_user_id: str,
        actor_role: str,
    ) -> dict:
        if not is_platform_admin(actor_role):
            raise ForbiddenError(
                message="Only platform admins can delete customer organizations"
            )

        return self.organization_deletion_service.delete_organization(
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            actor_role=actor_role,
        )
