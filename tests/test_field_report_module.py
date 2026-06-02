from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.auth.jwt_service import JWTService
from app.services.field_report_module_service import (
    FieldReportModuleService,
)
from app.services.field_report_organization_profile_service import (
    FieldReportOrganizationProfileService,
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
            "enabled_at": "2026-06-01T00:00:00+00:00" if is_enabled else None,
            "disabled_at": None if is_enabled else "2026-06-01T01:00:00+00:00",
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
            "org-2": {
                "id": "org-2",
                "organization_name": "Org Two",
                "contact_email": "two@example.com",
            },
        }

    def get_by_id(self, organization_id: str) -> dict | None:
        if organization_id == "missing":
            return None
        return self.organizations.get(organization_id, {
            "id": organization_id,
            "organization_name": "Test Org",
            "contact_email": "test@example.com",
        })

    def get_all_organizations(self) -> list[dict]:
        return list(self.organizations.values())

    def update_report_profile(self, *, organization_id: str, **kwargs) -> dict | None:
        organization = self.organizations.get(organization_id)
        if not organization:
            return None
        organization.update(kwargs)
        return organization


class FakeVisitReportRepository:
    def __init__(self) -> None:
        self.records_by_org: dict[str, list[dict]] = {}

    def is_storage_available(self) -> bool:
        return True

    def list_by_organization(
        self,
        organization_id: str,
        *,
        status: str | None = None,
    ) -> list[dict]:
        reports = list(self.records_by_org.get(organization_id, []))
        if status:
            reports = [
                report
                for report in reports
                if report.get("status") == status
            ]
        return reports

    def snapshot_for_org(self, organization_id: str) -> list[dict]:
        return [
            dict(record)
            for record in self.records_by_org.get(organization_id, [])
        ]


def test_module_service_enable_and_query():
    service = FieldReportModuleService(
        module_repository=FakeModuleRepository(),
        organization_repository=FakeOrganizationRepository(),
        visit_report_repository=FakeVisitReportRepository(),
    )

    assert service.is_enabled_for_organization("org-1") is False

    service.set_enabled(
        organization_id="org-1",
        is_enabled=True,
        actor_profile_id="admin-1",
    )

    assert service.is_enabled_for_organization("org-1") is True


def test_field_report_home_requires_enabled_module(monkeypatch):
    fake_repo = FakeModuleRepository()
    service = FieldReportModuleService(
        module_repository=fake_repo,
        organization_repository=FakeOrganizationRepository(),
        visit_report_repository=FakeVisitReportRepository(),
    )

    monkeypatch.setattr(
        "app.main.field_report_module_service",
        service,
    )

    app.state.field_report_module_service = service
    client = TestClient(app)
    token = _token()

    response = client.get(
        "/field-reports/home",
        headers=_headers(token),
    )
    assert response.status_code == 403

    service.set_enabled(
        organization_id="org-1",
        is_enabled=True,
        actor_profile_id="admin-1",
    )

    response = client.get(
        "/field-reports/home",
        headers=_headers(token),
    )
    assert response.status_code == 200
    assert response.json()["module"] == "field_reports"


def test_admin_module_list_and_toggle(monkeypatch):
    fake_repo = FakeModuleRepository()
    fake_visit_repo = FakeVisitReportRepository()
    fake_visit_repo.records_by_org = {
        "org-1": [
            {"id": "r-1", "status": "IN_PROGRESS"},
            {"id": "r-2", "status": "CLOSED"},
            {"id": "r-3", "status": "LOCKED"},
        ],
        "org-2": [
            {"id": "r-4", "status": "LOCKED"},
        ],
    }
    service = FieldReportModuleService(
        module_repository=fake_repo,
        organization_repository=FakeOrganizationRepository(),
        visit_report_repository=fake_visit_repo,
    )

    monkeypatch.setattr(
        "app.main.field_report_module_service",
        service,
    )

    client = TestClient(app)
    token = _token()

    list_response = client.get(
        "/admin/field-reports/modules",
        headers=_headers(token),
    )
    assert list_response.status_code == 200
    payload = list_response.json()
    assert payload["total"] == 2
    assert payload["organizations"][0]["is_enabled"] is False
    assert payload["organizations"][0]["unsent_drafts_count"] == 2
    assert payload["organizations"][1]["unsent_drafts_count"] == 0

    patch_response = client.patch(
        "/admin/field-reports/modules/org-2",
        headers=_headers(token),
        json={"is_enabled": True},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["is_enabled"] is True


def test_client_admin_cannot_toggle_module():
    client = TestClient(app)
    token = _token(role="ADMIN")

    response = client.patch(
        "/admin/field-reports/modules/org-1",
        headers=_headers(token),
        json={"is_enabled": True},
    )
    assert response.status_code == 403


def test_disabling_module_does_not_change_locked_reports():
    fake_module_repo = FakeModuleRepository()
    fake_visit_repo = FakeVisitReportRepository()
    fake_visit_repo.records_by_org = {
        "org-1": [
            {
                "id": "locked-1",
                "status": "LOCKED",
                "core_report_id": "core-1001",
                "locked_at": "2026-06-02T10:00:00+00:00",
            },
            {
                "id": "draft-1",
                "status": "CLOSED",
            },
        ]
    }
    service = FieldReportModuleService(
        module_repository=fake_module_repo,
        organization_repository=FakeOrganizationRepository(),
        visit_report_repository=fake_visit_repo,
    )

    # Baseline: report history before toggling module off.
    before = fake_visit_repo.snapshot_for_org("org-1")

    service.set_enabled(
        organization_id="org-1",
        is_enabled=False,
        actor_profile_id="admin-1",
    )

    after = fake_visit_repo.snapshot_for_org("org-1")
    assert after == before
    locked_reports = [
        report for report in after if report.get("status") == "LOCKED"
    ]
    assert len(locked_reports) == 1
    assert locked_reports[0]["core_report_id"] == "core-1001"


def test_admin_can_update_organization_report_profile(monkeypatch):
    fake_org_repo = FakeOrganizationRepository()
    module_service = FieldReportModuleService(
        module_repository=FakeModuleRepository(),
        organization_repository=fake_org_repo,
        visit_report_repository=FakeVisitReportRepository(),
    )
    profile_service = FieldReportOrganizationProfileService(
        organization_repository=fake_org_repo,
        module_service=module_service,
    )

    monkeypatch.setattr(
        "app.main.field_report_organization_profile_service",
        profile_service,
    )

    client = TestClient(app)
    token = _token()

    response = client.patch(
        "/admin/field-reports/organizations/org-1/profile",
        headers=_headers(token),
        json={
            "report_phone": "03-1234567",
            "report_address_line": "רחוב הבדיקה 10",
            "report_city": "תל אביב",
            "report_tagline": "פיקוח הנדסי מטעם הדיירים",
            "logo_storage_path": "/storage/v1/object/public/logos/org-1.png",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["organization_id"] == "org-1"
    assert payload["report_phone"] == "03-1234567"
    assert payload["report_city"] == "תל אביב"
    assert payload["logo_storage_path"].endswith("org-1.png")


def test_admin_can_get_organization_report_profile(monkeypatch):
    fake_org_repo = FakeOrganizationRepository()
    fake_org_repo.organizations["org-1"].update({
        "report_phone": "03-9876543",
        "report_address_line": "רחוב הבדיקה 1",
        "report_city": "חיפה",
        "report_tagline": "פיקוח הנדסי",
        "logo_storage_path": "/storage/v1/object/public/logos/org-1.svg",
    })
    module_service = FieldReportModuleService(
        module_repository=FakeModuleRepository(),
        organization_repository=fake_org_repo,
        visit_report_repository=FakeVisitReportRepository(),
    )
    profile_service = FieldReportOrganizationProfileService(
        organization_repository=fake_org_repo,
        module_service=module_service,
    )

    monkeypatch.setattr(
        "app.main.field_report_organization_profile_service",
        profile_service,
    )

    client = TestClient(app)
    token = _token()

    response = client.get(
        "/admin/field-reports/organizations/org-1/profile",
        headers=_headers(token),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["organization_id"] == "org-1"
    assert payload["report_phone"] == "03-9876543"
    assert payload["report_city"] == "חיפה"
    assert payload["logo_storage_path"].endswith("org-1.svg")
