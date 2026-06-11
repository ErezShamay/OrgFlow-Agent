from __future__ import annotations

from app.auth.roles import is_platform_admin
from app.exceptions.exceptions import (
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.repositories.organization_repository import (
    OrganizationRepository,
)
from app.repositories.profile_repository import (
    ProfileRepository,
)


class TenantAccessService:
    def __init__(
        self,
        profile_repository: ProfileRepository | None = None,
        organization_repository: OrganizationRepository | None = None,
    ) -> None:
        self.profile_repository = (
            profile_repository or ProfileRepository()
        )
        self.organization_repository = (
            organization_repository or OrganizationRepository()
        )

    def resolve_organization_access(
        self,
        *,
        profile_id: str,
        requested_organization_id: str | None = None,
    ) -> str:
        profile = self.profile_repository.get_profile_by_id(
            profile_id
        )

        if not profile:
            raise NotFoundError(
                message="Profile not found",
                resource_type="profile",
                resource_id=profile_id,
            )

        profile_org_id = (
            ProfileRepository.extract_organization_id(profile)
        )

        if requested_organization_id:
            requested_organization_id = (
                requested_organization_id.strip()
            )

            if not requested_organization_id:
                raise ValidationError(
                    message="organization_id cannot be empty"
                )

            if self.can_access_organization(
                profile_id=profile_id,
                organization_id=requested_organization_id,
                profile=profile,
            ):
                return requested_organization_id

            raise ForbiddenError(
                message="No access to the requested organization"
            )

        if profile_org_id:
            return profile_org_id

        raise ValidationError(
            message=(
                "Profile is not assigned to a customer organization. "
                "Run tenant migration or contact support."
            )
        )

    def can_access_organization(
        self,
        *,
        profile_id: str,
        organization_id: str,
        profile: dict | None = None,
    ) -> bool:
        profile = profile or self.profile_repository.get_profile_by_id(
            profile_id
        )

        if not profile:
            return False

        if is_platform_admin(profile.get("role")):
            organization = self.organization_repository.get_by_id(
                organization_id
            )
            return organization is not None

        profile_org_id = (
            ProfileRepository.extract_organization_id(profile)
        )

        return profile_org_id == organization_id

    def resolve_admin_target_organization(
        self,
        *,
        profile_id: str,
        role: str,
        session_org_id: str,
        requested_organization_id: str | None = None,
    ) -> str:
        if is_platform_admin(role):
            if requested_organization_id:
                return self.resolve_organization_access(
                    profile_id=profile_id,
                    requested_organization_id=(
                        requested_organization_id
                    ),
                )
            return session_org_id.strip()

        if (
            requested_organization_id
            and requested_organization_id.strip()
            != session_org_id.strip()
        ):
            raise ForbiddenError(
                message=(
                    "Organization admins can only manage "
                    "their own customer"
                )
            )

        return session_org_id.strip()

    def list_accessible_organizations(
        self,
        profile_id: str,
    ) -> list[dict]:
        profile = self.profile_repository.get_profile_by_id(
            profile_id
        )

        if profile and is_platform_admin(profile.get("role")):
            return self.organization_repository.get_all_organizations()

        profile_org_id = (
            ProfileRepository.extract_organization_id(profile)
            if profile
            else ""
        )

        if not profile_org_id:
            return []

        organization = self.organization_repository.get_by_id(
            profile_org_id
        )

        if not organization:
            return []

        return [organization]
