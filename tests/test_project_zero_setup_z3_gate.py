from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import app.main as main_module
from app.auth.jwt_service import JWTService
from app.config.project_template_seed import (
    DEFAULT_PUBLIC_AREA_IDS,
    seed_template_for_scheme,
)
from app.main import app
from app.services.project_spatial_bootstrap_service import (
    ProjectSpatialBootstrapService,
    build_apartment_bootstrap_rows,
    build_stable_apartment_number,
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

    def get_project_by_id(self, project_id: str) -> dict | None:
        return self.projects.get(project_id)

    def update_project(self, project_id: str, updates: dict) -> dict | None:
        project = self.projects.setdefault(project_id, {"id": project_id})
        project.update(updates)
        return project


class InMemoryProjectTemplateRepository:
    def __init__(self, records: list[dict] | None = None) -> None:
        self.records = list(records or [])

    def list_active_for_scheme(
        self,
        scheme: str,
        *,
        organization_id: str | None = None,
    ) -> list[dict]:
        results: list[dict] = []
        for record in self.records:
            if record.get("scheme") != scheme:
                continue
            if not record.get("is_active", True):
                continue
            record_org = record.get("organization_id")
            if organization_id:
                if record_org not in (None, organization_id):
                    continue
            elif record_org is not None:
                continue
            results.append(record)
        return results

    def get_by_id(self, template_id: str) -> dict | None:
        for record in self.records:
            if str(record.get("id")) == template_id:
                return record
        return None


def _auth_headers() -> dict[str, str]:
    token = JWTService().issue_access_token(
        user_id="admin-z3",
        org_id="org-z3",
        role="ADMIN",
        token_id="project-zero-setup-z3",
    )
    return {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": "org-z3",
    }


def _bootstrap_service(
    *,
    apartments: InMemoryProjectApartmentRepository | None = None,
    projects: InMemoryProjectRepository | None = None,
) -> ProjectSpatialBootstrapService:
    apartment_repository = apartments or InMemoryProjectApartmentRepository()
    project_repository = projects or InMemoryProjectRepository()
    template_service = ProjectTemplateService(
        repository=InMemoryProjectTemplateRepository(
            [seed_template_for_scheme("TAMA38_STRENGTHENING") or {}]
        )
    )
    return ProjectSpatialBootstrapService(
        template_service=template_service,
        apartment_repository=apartment_repository,
        project_repository=project_repository,
    )


def test_build_stable_apartment_number_seven_by_four() -> None:
    numbers = [
        build_stable_apartment_number(floor, unit, units_per_floor=4)
        for floor in range(1, 8)
        for unit in range(1, 5)
    ]

    assert len(numbers) == 28
    assert numbers[0] == "1"
    assert numbers[3] == "4"
    assert numbers[4] == "5"
    assert numbers[-1] == "28"
    assert len(set(numbers)) == 28


def test_bootstrap_creates_twenty_eight_apartments_for_tama38_template() -> None:
    apartments = InMemoryProjectApartmentRepository()
    projects = InMemoryProjectRepository()
    projects.projects["proj-z3"] = {
        "id": "proj-z3",
        "scheme": "TAMA38_STRENGTHENING",
    }
    service = _bootstrap_service(apartments=apartments, projects=projects)

    result = service.bootstrap(
        project_id="proj-z3",
        scheme="TAMA38_STRENGTHENING",
        organization_id="org-z3",
    )

    assert result.skipped is False
    assert result.apartments_created == 28
    assert result.floors == 7
    assert result.units_per_floor == 4
    assert result.public_areas == list(DEFAULT_PUBLIC_AREA_IDS)
    assert len(apartments.list_by_project("proj-z3")) == 28
    assert projects.projects["proj-z3"]["spatial_public_area_ids"] == list(
        DEFAULT_PUBLIC_AREA_IDS
    )


def test_bootstrap_is_idempotent_when_apartments_exist() -> None:
    apartments = InMemoryProjectApartmentRepository()
    apartments.records = [
        {
            "id": "apt-existing",
            "project_id": "proj-z3",
            "organization_id": "org-z3",
            "apartment_number": "1",
        }
    ]
    projects = InMemoryProjectRepository()
    projects.projects["proj-z3"] = {
        "id": "proj-z3",
        "spatial_public_area_ids": ["LOBBY"],
    }
    service = _bootstrap_service(apartments=apartments, projects=projects)

    first = service.bootstrap(
        project_id="proj-z3",
        scheme="TAMA38_STRENGTHENING",
        organization_id="org-z3",
    )
    second = service.bootstrap(
        project_id="proj-z3",
        scheme="TAMA38_STRENGTHENING",
        organization_id="org-z3",
    )

    assert first.skipped is True
    assert first.apartments_created == 0
    assert second.skipped is True
    assert second.apartments_created == 0
    assert len(apartments.list_by_project("proj-z3")) == 1


def test_build_apartment_bootstrap_rows_count_matches_layout() -> None:
    rows = build_apartment_bootstrap_rows(floors=7, units_per_floor=4)
    assert len(rows) == 28
    assert rows[0]["apartment_number"] == "1"
    assert rows[-1]["apartment_number"] == "28"


def test_bootstrap_spatial_api_is_idempotent(monkeypatch) -> None:
    apartments = InMemoryProjectApartmentRepository()
    projects = InMemoryProjectRepository()
    projects.projects["proj-z3"] = {
        "id": "proj-z3",
        "scheme": "TAMA38_STRENGTHENING",
        "organization_id": "org-z3",
    }
    service = _bootstrap_service(apartments=apartments, projects=projects)

    class FakeTenantScope:
        def get_organization_scoped_project(self, project_id, *_args, **_kwargs):
            return projects.projects.get(project_id)

    monkeypatch.setattr(deps, "tenant_scope_service", FakeTenantScope())
    monkeypatch.setattr(deps, "project_spatial_bootstrap_service", service)
    client = TestClient(app)

    first = client.post(
        "/projects/proj-z3/bootstrap-spatial",
        headers=_auth_headers(),
    )
    second = client.post(
        "/projects/proj-z3/bootstrap-spatial",
        headers=_auth_headers(),
    )

    assert first.status_code == 200
    assert first.json()["apartments_created"] == 28
    assert second.status_code == 200
    assert second.json()["skipped"] is True
    assert second.json()["apartments_created"] == 0
    assert len(apartments.list_by_project("proj-z3")) == 28
