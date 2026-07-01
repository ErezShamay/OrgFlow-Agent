from __future__ import annotations

from fastapi.testclient import TestClient

import app.main as main_module
from app.auth.jwt_service import JWTService
from app.config.field_report_project_scheme import parse_project_scheme
from app.exceptions.exceptions import ValidationError
from app.main import app
from app.services.project_service import ProjectService
from tests.fixtures.project_create_payload import valid_create_project_payload
import app.dependencies as deps


class RecordingProjectService:
    def __init__(self) -> None:
        self.last_create_payload: dict | None = None

    def create_project(self, **payload):
        self.last_create_payload = payload
        return {"id": "proj-z1", "status": "ACTIVE", **payload}


def _auth_headers() -> dict[str, str]:
    token = JWTService().issue_access_token(
        user_id="admin-z1",
        org_id="org-z1",
        role="ADMIN",
        token_id="project-zero-setup-z1",
    )
    return {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": "org-z1",
    }


def _valid_create_payload() -> dict:
    return valid_create_project_payload()


def test_parse_project_scheme_accepts_all_four_schemes() -> None:
    for scheme in (
        "TAMA38_STRENGTHENING",
        "TAMA38_DEMOLITION_REBUILD",
        "TAMA38_RELOCATED_BUILD",
        "NEW_CONSTRUCTION",
    ):
        assert parse_project_scheme(scheme) == scheme


def test_parse_project_scheme_rejects_missing_or_invalid() -> None:
    for value in (None, "", "INVALID_SCHEME"):
        try:
            parse_project_scheme(value)
        except ValueError as error:
            assert "scheme" in str(error).lower()
        else:
            raise AssertionError(f"expected ValueError for {value!r}")


def test_create_project_requires_scheme(monkeypatch) -> None:
    monkeypatch.setattr(deps, "project_service", RecordingProjectService())
    client = TestClient(app)

    payload = _valid_create_payload()
    del payload["scheme"]

    response = client.post(
        "/projects",
        json=payload,
        headers=_auth_headers(),
    )

    assert response.status_code == 422


def test_create_project_rejects_invalid_scheme(monkeypatch) -> None:
    monkeypatch.setattr(deps, "project_service", RecordingProjectService())
    client = TestClient(app)

    payload = _valid_create_payload()
    payload["scheme"] = "NOT_A_REAL_SCHEME"

    response = client.post(
        "/projects",
        json=payload,
        headers=_auth_headers(),
    )

    assert response.status_code == 422


def test_create_project_rejects_invalid_project_dates(monkeypatch) -> None:
    monkeypatch.setattr(deps, "project_service", RecordingProjectService())
    client = TestClient(app)

    payload = _valid_create_payload()
    payload["project_start_date"] = "2028-12-01"
    payload["project_end_date"] = "2026-01-01"

    response = client.post(
        "/projects",
        json=payload,
        headers=_auth_headers(),
    )

    assert response.status_code == 422


def test_create_project_rejects_grace_before_end(monkeypatch) -> None:
    monkeypatch.setattr(deps, "project_service", RecordingProjectService())
    client = TestClient(app)

    payload = _valid_create_payload()
    payload["project_grace_end_date"] = "2026-01-01"

    response = client.post(
        "/projects",
        json=payload,
        headers=_auth_headers(),
    )

    assert response.status_code == 422


def test_create_project_with_valid_scheme_passes_to_service(monkeypatch) -> None:
    service = RecordingProjectService()
    monkeypatch.setattr(deps, "project_service", service)
    client = TestClient(app)

    payload = _valid_create_payload()
    payload["floors_count"] = 7
    payload["housing_units_count"] = 28

    response = client.post(
        "/projects",
        json=payload,
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    assert service.last_create_payload is not None
    assert service.last_create_payload["scheme"] == "TAMA38_STRENGTHENING"
    assert service.last_create_payload["floors_count"] == 7
    assert service.last_create_payload["housing_units_count"] == 28


def test_project_service_create_rejects_missing_scheme() -> None:
    service = ProjectService()

    try:
        service.create_project(
            project_name="Tower",
            developer_name="Dev",
            contractor_name="Build",
            lawyer_name="Legal",
            supervisor_name="Noa",
            supervisor_email="noa@example.com",
            scheme=None,
        )
    except ValidationError as error:
        assert "scheme" in str(error).lower()
    else:
        raise AssertionError("expected ValidationError")


def test_edit_project_rejects_invalid_scheme(monkeypatch) -> None:
    class FakeTenantScope:
        def get_organization_scoped_project(self, *_args, **_kwargs):
            return {"id": "p1"}

    monkeypatch.setattr(deps, "tenant_scope_service", FakeTenantScope())
    monkeypatch.setattr(
        deps.project_service,
        "edit_project",
        lambda *_args, **_kwargs: {"id": "p1"},
    )
    client = TestClient(app)

    response = client.patch(
        "/projects/p1",
        json={"scheme": "INVALID"},
        headers=_auth_headers(),
    )

    assert response.status_code == 422
