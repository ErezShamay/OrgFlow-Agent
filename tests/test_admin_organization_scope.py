from __future__ import annotations

import pytest

from app.auth.roles import PLATFORM_ADMIN_ROLE
from app.exceptions.exceptions import ForbiddenError
from app.services.tenant_access_service import TenantAccessService


class FakeProfileRepository:
    def get_profile_by_id(self, profile_id: str):
        if profile_id == "platform-admin":
            return {
                "id": profile_id,
                "role": PLATFORM_ADMIN_ROLE,
                "organization_id": "org-demo",
            }
        return {
            "id": profile_id,
            "role": "ADMIN",
            "organization_id": "org-client",
        }


class FakeOrganizationRepository:
    def get_by_id(self, organization_id: str):
        return {"id": organization_id}

    def profile_owns_organization(
        self,
        *,
        profile_id: str,
        organization_id: str,
    ) -> bool:
        return False


@pytest.fixture
def tenant_access_service() -> TenantAccessService:
    return TenantAccessService(
        profile_repository=FakeProfileRepository(),
        organization_repository=FakeOrganizationRepository(),
    )


def test_platform_admin_can_target_explicit_organization(
    tenant_access_service: TenantAccessService,
):
    org_id = tenant_access_service.resolve_admin_target_organization(
        profile_id="platform-admin",
        role=PLATFORM_ADMIN_ROLE,
        session_org_id="org-demo",
        requested_organization_id="org-new-client",
    )

    assert org_id == "org-new-client"


def test_org_admin_cannot_target_different_organization(
    tenant_access_service: TenantAccessService,
):
    with pytest.raises(ForbiddenError):
        tenant_access_service.resolve_admin_target_organization(
            profile_id="client-admin",
            role="ADMIN",
            session_org_id="org-client",
            requested_organization_id="org-demo",
        )


def test_org_admin_cannot_access_other_organization_even_when_owner(
    tenant_access_service: TenantAccessService,
):
    service = TenantAccessService(
        profile_repository=FakeProfileRepository(),
        organization_repository=FakeOrganizationRepository(),
    )
    service.organization_repository.profile_owns_organization = (
        lambda **_: True
    )

    assert service.can_access_organization(
        profile_id="client-admin",
        organization_id="org-demo",
    ) is False


def test_org_admin_lists_only_assigned_organization(
    tenant_access_service: TenantAccessService,
):
    organizations = tenant_access_service.list_accessible_organizations(
        "client-admin"
    )

    assert organizations == [{"id": "org-client"}]
