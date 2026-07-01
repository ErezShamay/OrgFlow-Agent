from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from postgrest.exceptions import APIError

import app.main as main_module
from app.auth.jwt_service import JWTService
from app.config.project_template_seed import (
    DEFAULT_PUBLIC_AREA_IDS,
    PROJECT_TEMPLATE_SEED,
    TAMA38_STRENGTHENING_TEMPLATE_ID,
    seed_template_for_scheme,
)
from app.db.schema_registry import MIGRATION_SCRIPTS, SCHEMA_VERSION, TABLES
from app.exceptions.exceptions import NotFoundError
from app.main import app
from app.repositories.project_template_repository import (
    PROJECT_TEMPLATES_MIGRATION,
    ProjectTemplateRepository,
)
from app.schemas.project_template import ProjectTemplate
from app.services.project_template_service import ProjectTemplateService
import app.dependencies as deps


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
        user_id="admin-z2",
        org_id="org-z2",
        role="ADMIN",
        token_id="project-zero-setup-z2",
    )
    return {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": "org-z2",
    }


def test_migration_sql_defines_project_templates_table() -> None:
    migration_path = (
        Path(__file__).resolve().parents[1] / PROJECT_TEMPLATES_MIGRATION
    )
    sql = migration_path.read_text(encoding="utf-8")

    assert "CREATE TABLE" in sql
    assert "project_templates" in sql
    assert "public_area_ids" in sql
    assert "catalog_filter" in sql
    assert "project_templates_authenticated_select" in sql


def test_migration_registered_in_schema_registry() -> None:
    assert SCHEMA_VERSION == "2026061803"

    entry = next(
        script
        for script in MIGRATION_SCRIPTS
        if script["version"] == "2026061801"
    )
    assert entry["name"] == "project_templates"
    assert entry["tables"] == ["project_templates"]

    schema = TABLES["project_templates"]
    assert schema.tenant_column == "organization_id"
    assert "organization_id IS NULL" in schema.rls_policies[0].using_expression


def test_seed_template_tama38_strengthening_defaults() -> None:
    template = seed_template_for_scheme("TAMA38_STRENGTHENING")
    assert template is not None
    assert template["id"] == TAMA38_STRENGTHENING_TEMPLATE_ID
    assert template["default_floors"] == 7
    assert template["default_units_per_floor"] == 4
    assert template["public_area_ids"] == list(DEFAULT_PUBLIC_AREA_IDS)
    assert len(PROJECT_TEMPLATE_SEED) >= 1


def test_project_template_schema_validates_public_area_ids() -> None:
    template = ProjectTemplate.from_record(
        seed_template_for_scheme("TAMA38_STRENGTHENING") or {}
    )
    assert template.public_area_ids == list(DEFAULT_PUBLIC_AREA_IDS)

    with pytest.raises(ValueError):
        ProjectTemplate.from_record(
            {
                "id": "bad",
                "scheme": "TAMA38_STRENGTHENING",
                "template_name_he": "test",
                "public_area_ids": ["UNKNOWN_AREA"],
            }
        )


def test_service_resolve_prefers_organization_template() -> None:
    org_template = {
        "id": "org-template-1",
        "organization_id": "org-z2",
        "scheme": "TAMA38_STRENGTHENING",
        "template_name_he": "תבנית ארגון",
        "default_floors": 5,
        "default_units_per_floor": 2,
        "public_area_ids": ["LOBBY"],
        "is_active": True,
    }
    global_template = {
        **(seed_template_for_scheme("TAMA38_STRENGTHENING") or {}),
        "default_floors": 7,
    }
    service = ProjectTemplateService(
        repository=InMemoryProjectTemplateRepository(
            [global_template, org_template]
        )
    )

    resolved = service.resolve_for_scheme(
        "TAMA38_STRENGTHENING",
        organization_id="org-z2",
    )

    assert resolved.source == "organization"
    assert resolved.template.default_floors == 5


def test_service_resolve_falls_back_to_global_seed() -> None:
    service = ProjectTemplateService(
        repository=InMemoryProjectTemplateRepository(
            [seed_template_for_scheme("TAMA38_STRENGTHENING") or {}]
        )
    )

    resolved = service.resolve_for_scheme(
        "TAMA38_STRENGTHENING",
        organization_id="org-z2",
    )

    assert resolved.source == "global"
    assert resolved.template.default_units_per_floor == 4


def test_service_resolve_missing_scheme_raises_not_found() -> None:
    service = ProjectTemplateService(
        repository=InMemoryProjectTemplateRepository([])
    )

    with pytest.raises(NotFoundError):
        service.resolve_for_scheme("NEW_CONSTRUCTION")


def test_repository_seed_fallback_when_table_missing(monkeypatch) -> None:
    class BrokenClient:
        def table(self, _name: str):
            raise APIError({"message": "project_templates does not exist"})

    repository = ProjectTemplateRepository()
    monkeypatch.setattr(repository, "client", BrokenClient())

    records = repository.list_active_for_scheme("TAMA38_STRENGTHENING")

    assert len(records) == 1
    assert records[0]["scheme"] == "TAMA38_STRENGTHENING"


def test_resolve_project_template_api(monkeypatch) -> None:
    service = ProjectTemplateService(
        repository=InMemoryProjectTemplateRepository(
            [seed_template_for_scheme("TAMA38_STRENGTHENING") or {}]
        )
    )
    monkeypatch.setattr(deps, "project_template_service", service)
    client = TestClient(app)

    response = client.get(
        "/project-templates/resolve",
        params={"scheme": "TAMA38_STRENGTHENING"},
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["template"]["scheme"] == "TAMA38_STRENGTHENING"
    assert payload["template"]["default_floors"] == 7
