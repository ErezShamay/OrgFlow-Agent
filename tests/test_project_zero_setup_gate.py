from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import app.main as main_module
from app.auth.jwt_service import JWTService
from app.config.project_template_seed import seed_template_for_scheme
from app.main import app
from app.services.field_visit_report_service import FieldVisitReportService
from app.services.project_spatial_bootstrap_service import (
    ProjectSpatialBootstrapService,
    build_apartment_bootstrap_rows,
)
from app.services.project_template_service import ProjectTemplateService
import app.dependencies as deps


class InMemoryProjectApartmentRepository:
    def __init__(self) -> None:
        self.records: list[dict] = []

    def is_storage_available(self) -> bool:
        return True

    def list_by_project(self, project_id: str) -> list[dict]:
        return [
            record
            for record in self.records
            if str(record.get("project_id")) == project_id
        ]

    def bulk_create_apartments(
        self,
        *,
        organization_id: str,
        project_id: str,
        apartments: list[dict],
    ) -> list[dict]:
        created: list[dict] = []
        for index, item in enumerate(apartments, start=1):
            row = {
                "id": f"apt-{project_id}-{index}",
                "organization_id": organization_id,
                "project_id": project_id,
                "apartment_number": item["apartment_number"],
                "group_key": f"apartment:{item['apartment_number']}",
                "owner_name": item.get("owner_name", "דייר"),
            }
            self.records.append(row)
            created.append(row)
        return created


class InMemoryProjectRepository:
    def __init__(self) -> None:
        self.projects: dict[str, dict] = {}
        self._next_id = 1

    def create_project(self, **payload) -> dict:
        project_id = f"proj-z4-{self._next_id}"
        self._next_id += 1
        project = {"id": project_id, **payload}
        self.projects[project_id] = project
        return project

    def get_project_by_id(self, project_id: str) -> dict | None:
        return self.projects.get(project_id)

    def get_projects_by_organization(self, organization_id: str) -> list[dict]:
        return [
            project
            for project in self.projects.values()
            if str(project.get("organization_id")) == organization_id
        ]

    def update_project(self, project_id: str, updates: dict) -> dict | None:
        project = self.projects.setdefault(project_id, {"id": project_id})
        project.update(updates)
        return project


class InMemoryProjectTemplateRepository:
    def list_active_for_scheme(
        self,
        scheme: str,
        *,
        organization_id: str | None = None,
    ) -> list[dict]:
        template = seed_template_for_scheme(scheme)
        return [template] if template else []

    def get_by_id(self, template_id: str) -> dict | None:
        for template in [seed_template_for_scheme("TAMA38_STRENGTHENING")]:
            if template and str(template.get("id")) == template_id:
                return template
        return None


class ZeroSetupProjectService:
    def __init__(
        self,
        *,
        project_repository: InMemoryProjectRepository,
        apartment_repository: InMemoryProjectApartmentRepository,
    ) -> None:
        self.project_repository = project_repository
        self.spatial_bootstrap_service = ProjectSpatialBootstrapService(
            template_service=ProjectTemplateService(
                repository=InMemoryProjectTemplateRepository()
            ),
            apartment_repository=apartment_repository,
            project_repository=project_repository,
        )

    def create_project(self, **payload):
        normalized_scheme = payload["scheme"]
        project = self.project_repository.create_project(**payload)
        org_id = str(project.get("organization_id") or "")
        if org_id:
            bootstrap = self.spatial_bootstrap_service.bootstrap(
                project_id=str(project["id"]),
                scheme=normalized_scheme,
                organization_id=org_id,
                floors=payload.get("floors_count"),
                housing_units_count=payload.get("housing_units_count"),
            )
            project = {
                **project,
                "spatial_bootstrap": bootstrap.model_dump(),
            }
        return project


def _auth_headers() -> dict[str, str]:
    token = JWTService().issue_access_token(
        user_id="admin-z4",
        org_id="org-z4",
        role="ADMIN",
        token_id="project-zero-setup-z4",
    )
    return {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": "org-z4",
    }


def test_zero_setup_create_project_spatial_bootstrap_and_offline_prep(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_repository = InMemoryProjectRepository()
    apartment_repository = InMemoryProjectApartmentRepository()
    project_service = ZeroSetupProjectService(
        project_repository=project_repository,
        apartment_repository=apartment_repository,
    )

    report_repository = MagicMock()
    report_repository.is_storage_available.return_value = True
    report_repository.list_by_organization.return_value = []

    catalog_service = MagicMock()
    catalog_service.get_full_catalog.return_value = {
        "catalog_version": "1.4.0-supervision-checklist",
        "issues": [
            {
                "issue_id": "SUP-FIN-004",
                "issue_name_he": "פוגות",
                "standard_ref": 'ת"י 1555',
                "top_family": "FINISHING_WORKS",
                "category_id": "TILING",
                "category_name_he": "ריצוף",
                "scope": "APARTMENT",
                "allowed_stages": ["FINISHING"],
            }
        ],
    }

    organization_profile_service = MagicMock()
    organization_profile_service.get_profile.return_value = {}

    field_visit_report_service = FieldVisitReportService(
        report_repository=report_repository,
        project_repository=project_repository,
        apartment_repository=apartment_repository,
        organization_profile_service=organization_profile_service,
        catalog_service=catalog_service,
    )
    monkeypatch.setattr(field_visit_report_service, "are_lines_available", lambda: True)

    created = project_service.create_project(
        project_name="Tower Z4",
        developer_name="Dev",
        contractor_name="Build",
        lawyer_name="Legal",
        supervisor_name="Noa",
        organization_id="org-z4",
        scheme="TAMA38_STRENGTHENING",
        floors_count=7,
        housing_units_count=28,
        status="ACTIVE",
    )

    project_id = str(created["id"])
    assert created["spatial_bootstrap"]["apartments_created"] == 28
    assert len(apartment_repository.list_by_project(project_id)) == 28

    org_bundle = field_visit_report_service.build_offline_prep_bundle("org-z4")
    assert org_bundle["supervision_catalog"]["issue_count"] == 1
    assert len(org_bundle["apartments_by_project"][project_id]) == 28

    project_bundle = (
        field_visit_report_service.build_offline_prep_bundle_for_project(
            "org-z4",
            project_id,
        )
    )
    assert project_bundle["focused_project_id"] == project_id
    assert len(project_bundle["projects"]) == 1
    assert len(project_bundle["apartments_by_project"][project_id]) == 28
    assert project_bundle["reports"] == []


def test_build_offline_prep_bundle_for_project_rejects_foreign_org() -> None:
    project_repository = InMemoryProjectRepository()
    project_repository.projects["proj-foreign"] = {
        "id": "proj-foreign",
        "organization_id": "other-org",
    }

    service = FieldVisitReportService(
        report_repository=MagicMock(is_storage_available=lambda: True),
        project_repository=project_repository,
        apartment_repository=MagicMock(is_storage_available=lambda: False),
        organization_profile_service=MagicMock(),
        catalog_service=MagicMock(),
    )

    with pytest.raises(Exception):
        service.build_offline_prep_bundle_for_project("org-z4", "proj-foreign")


def test_project_offline_prep_api(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.main import app
    from app.services.field_report_module_service import FieldReportModuleService
    from tests.test_field_visit_reports import (
        FakeModuleRepository,
        FakeOrganizationRepository,
    )

    project_repository = InMemoryProjectRepository()
    apartment_repository = InMemoryProjectApartmentRepository()
    project_id = "proj-z4-api"
    project_repository.projects[project_id] = {
        "id": project_id,
        "organization_id": "org-z4",
        "project_name": "Tower",
        "scheme": "TAMA38_STRENGTHENING",
    }
    rows = build_apartment_bootstrap_rows(floors=7, units_per_floor=4)
    apartment_repository.bulk_create_apartments(
        organization_id="org-z4",
        project_id=project_id,
        apartments=rows,
    )

    report_repository = MagicMock()
    report_repository.is_storage_available.return_value = True
    report_repository.list_by_organization.return_value = []

    catalog_service = MagicMock()
    catalog_service.get_full_catalog.return_value = {
        "catalog_version": "gate-v1",
        "issues": [],
    }

    field_visit_report_service = FieldVisitReportService(
        report_repository=report_repository,
        project_repository=project_repository,
        apartment_repository=apartment_repository,
        organization_profile_service=MagicMock(get_profile=lambda *_a, **_k: {}),
        catalog_service=catalog_service,
    )
    monkeypatch.setattr(field_visit_report_service, "are_lines_available", lambda: True)

    module_repository = FakeModuleRepository()
    module_repository.records["org-z4"] = {
        "organization_id": "org-z4",
        "is_enabled": True,
    }
    module_service = FieldReportModuleService(
        module_repository=module_repository,
        organization_repository=FakeOrganizationRepository(),
    )

    class FakeTenantScope:
        def get_organization_scoped_project(self, pid, *_args, **_kwargs):
            return project_repository.projects.get(pid)

    monkeypatch.setattr(deps, "tenant_scope_service", FakeTenantScope())
    monkeypatch.setattr(
        deps,
        "field_visit_report_service",
        field_visit_report_service,
    )
    monkeypatch.setattr(
        deps,
        "field_report_module_service",
        module_service,
    )
    app.state.field_report_module_service = module_service

    client = TestClient(app)
    response = client.get(
        f"/projects/{project_id}/offline-prep",
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["focused_project_id"] == project_id
    assert len(payload["apartments_by_project"][project_id]) == 28
