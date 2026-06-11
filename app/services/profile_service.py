from postgrest.exceptions import APIError

from app.auth.roles import is_platform_admin
from app.config.settings import settings
from app.repositories.organization_repository import (
    OrganizationRepository,
)
from app.repositories.profile_repository import (
    ProfileRepository,
)
from app.services.tenant_access_service import (
    TenantAccessService,
)

PROFILE_ORG_ID_KEYS = (
    "organization_id",
    "org_id",
)


class ProfileService:

    def __init__(
        self,
        organization_repository:
            OrganizationRepository | None = None,
        profile_repository: ProfileRepository | None = None,
        tenant_access_service: TenantAccessService | None = None,
    ):

        self.repository = (
            profile_repository or ProfileRepository()
        )
        self.organization_repository = (
            organization_repository
            or OrganizationRepository()
        )
        self.tenant_access_service = (
            tenant_access_service or TenantAccessService()
        )

    def get_profile(
        self,
        profile_id: str,
    ):

        return (
            self.repository
            .get_profile_by_id(
                profile_id
            )
        )

    def _extract_organization_id(
        self,
        profile: dict,
    ) -> str:

        return ProfileRepository.extract_organization_id(
            profile
        )

    def ensure_organization_id(
        self,
        profile_id: str,
        *,
        preferred_organization_id: str | None = None,
    ) -> str | None:

        profile = self.get_profile(profile_id)

        if not profile:
            return None

        if preferred_organization_id:
            return (
                self.tenant_access_service
                .resolve_organization_access(
                    profile_id=profile_id,
                    requested_organization_id=(
                        preferred_organization_id
                    ),
                )
            )

        org_id = self._extract_organization_id(profile)

        if org_id:
            return org_id

        if is_platform_admin(profile.get("role")):
            organizations = (
                self.organization_repository.get_all_organizations()
            )
            if organizations:
                return str(organizations[0]["id"]).strip()

        if not self.repository.supports_organization_column():
            if settings.ENVIRONMENT in {
                "local",
                "development",
                "test",
            }:
                organization = (
                    self.organization_repository
                    .get_first_organization()
                )

                if not organization:
                    organization = (
                        self.organization_repository
                        .create_organization(
                            name="Default Customer",
                            contact_email="demo@example.com",
                            owner_profile_id=profile_id,
                        )
                    )

                return str(organization["id"]).strip()

            return None

        return None

    def is_admin(
        self,
        profile_id: str,
    ):

        profile = (
            self.get_profile(
                profile_id
            )
        )

        if not profile:

            return False

        return (
            str(profile.get("role") or "").strip().upper()
            in {
                "ADMIN",
                "PLATFORM_ADMIN",
            }
        )

    def is_manager(
        self,
        profile_id: str,
    ):

        profile = (
            self.get_profile(
                profile_id
            )
        )

        if not profile:

            return False

        return (
            str(profile.get("role") or "").strip().upper()
            in [
                "ADMIN",
                "PLATFORM_ADMIN",
                "SUPERVISOR",
                "MANAGER",
            ]
        )
