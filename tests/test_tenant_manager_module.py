from __future__ import annotations

from fastapi.testclient import TestClient

from app.auth.jwt_service import JWTService
from app.main import app
from app.services.tenant_manager_module_service import (
    TenantManagerModuleService,
)


def _token(
    *,
    user_id: str = "admin-1",
    org_id: str = "org-1",
    role: str = "PLATFORM_ADMIN",
) -> str:
    return JWTService().issue_access_token(
        user_id=user_id,
        org_id=org_id,
        role=role,
        token_id="t-1",
    )


def _headers(token: str, org_id: str = "org-1") -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": org_id,
    }


class FakeModuleRepository:
    def __init__(self) -> None:
        self.records: dict[str, dict] = {}
        self._available = True

    def is_storage_available(self) -> bool:
        return self._available

    def get_by_organization_id(self, organization_id: str) -> dict | None:
        return self.records.get(organization_id)

    def list_all(self) -> list[dict]:
        return list(self.records.values())

    def upsert_status(
        self,
        *,
        organization_id: str,
        is_enabled: bool,
        enabled_by_profile_id: str | None,
    ) -> dict:
        record = {
            "organization_id": organization_id,
            "is_enabled": is_enabled,
            "enabled_at": "2026-06-11T00:00:00+00:00" if is_enabled else None,
            "disabled_at": None if is_enabled else "2026-06-11T01:00:00+00:00",
            "enabled_by_profile_id": enabled_by_profile_id,
        }
        self.records[organization_id] = record
        return record


class FakeOrganizationRepository:
    def __init__(self) -> None:
        self.organizations: dict[str, dict] = {
            "org-1": {
                "id": "org-1",
                "organization_name": "Org One",
                "contact_email": "one@example.com",
            },
        }

    def get_all_organizations(self) -> list[dict]:
        return list(self.organizations.values())

    def get_by_id(self, organization_id: str) -> dict | None:
        return self.organizations.get(organization_id)


def test_tenant_manager_module_status_defaults_disabled(monkeypatch) -> None:
    repository = FakeModuleRepository()
    service = TenantManagerModuleService(
        module_repository=repository,
        organization_repository=FakeOrganizationRepository(),
    )
    monkeypatch.setattr(
        "app.dependencies.tenant_manager_module_service",
        service,
    )
    app.state.tenant_manager_module_service = service

    client = TestClient(app)
    response = client.get(
        "/tenant-manager/module-status",
        headers=_headers(_token()),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["organization_id"] == "org-1"
    assert payload["is_enabled"] is False


def test_platform_admin_can_enable_tenant_manager_module(monkeypatch) -> None:
    repository = FakeModuleRepository()
    service = TenantManagerModuleService(
        module_repository=repository,
        organization_repository=FakeOrganizationRepository(),
    )
    monkeypatch.setattr(
        "app.dependencies.tenant_manager_module_service",
        service,
    )
    app.state.tenant_manager_module_service = service

    client = TestClient(app)
    response = client.patch(
        "/admin/tenant-manager/modules/org-1",
        headers=_headers(_token()),
        json={"is_enabled": True},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_enabled"] is True
    assert repository.records["org-1"]["is_enabled"] is True
