from __future__ import annotations

import json
import zipfile
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.auth.jwt_service import JWTService
from app.main import app
from app.services.field_visit_report_export_service import (
    FieldVisitReportExportService,
)
from app.services.field_visit_report_pdf_service import (
    FieldVisitReportPdfService,
)
from tests.test_field_visit_reports import (
    FakeProjectRepository,
    FakeVisitReportRepository,
)


FAKE_PDF = b"%PDF-1.4\narchived-report\n%%EOF\n"


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
        token_id="export-test-1",
    )


def _headers(token: str, org_id: str = "org-1") -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": org_id,
    }


class FakeOrganizationRepository:
    def __init__(self) -> None:
        self.organizations = {
            "org-1": {
                "id": "org-1",
                "organization_name": "לקוח א",
            }
        }

    def get_by_id(self, organization_id: str):
        return self.organizations.get(organization_id)


def test_export_organization_pdfs_zip_builds_project_folders(
    tmp_path: Path,
):
    pdf_service = FieldVisitReportPdfService(
        pdfs_root=tmp_path / "field_report_pdfs"
    )
    storage_path, _ = pdf_service.save_pdf(
        organization_id="org-1",
        project_id="project-1",
        report_id="report-1",
        content=FAKE_PDF,
        filename="march.pdf",
    )

    fake_repo = FakeVisitReportRepository()
    fake_repo.records["report-1"] = {
        "id": "report-1",
        "organization_id": "org-1",
        "project_id": "project-1",
        "visit_date": "2025-03-15",
        "visit_type": "STRUCTURE_SITE",
        "status": "LOCKED",
        "pdf_storage_path": storage_path,
        "pdf_filename": "march.pdf",
    }

    project_repo = FakeProjectRepository()

    service = FieldVisitReportExportService(
        report_repository=fake_repo,
        project_repository=project_repo,
        organization_repository=FakeOrganizationRepository(),
        pdf_service=pdf_service,
    )

    content, filename = service.export_organization_pdfs_zip("org-1")

    assert filename.startswith("field-reports_")
    assert filename.endswith(".zip")

    with zipfile.ZipFile(BytesIO(content)) as archive:
        names = archive.namelist()
        assert "manifest.json" in names
        assert any(name.endswith("march.pdf") for name in names)
        assert any(name.startswith("פרויקט_בדיקה/") for name in names)

        manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
        assert manifest["total_included"] == 1
        assert manifest["organization_name"] == "לקוח א"


def test_export_organization_pdfs_zip_raises_when_no_reports():
    fake_repo = FakeVisitReportRepository()

    service = FieldVisitReportExportService(
        report_repository=fake_repo,
        project_repository=FakeProjectRepository(),
        organization_repository=FakeOrganizationRepository(),
        pdf_service=FieldVisitReportPdfService(
            pdfs_root=Path("unused")
        ),
    )

    with pytest.raises(Exception) as error:
        service.export_organization_pdfs_zip("org-1")

    assert "לא נמצאו דוחות" in str(error.value)


def _build_export_service(tmp_path: Path) -> FieldVisitReportExportService:
    pdf_service = FieldVisitReportPdfService(
        pdfs_root=tmp_path / "field_report_pdfs"
    )
    storage_path, _ = pdf_service.save_pdf(
        organization_id="org-1",
        project_id="project-1",
        report_id="report-1",
        content=FAKE_PDF,
        filename="march.pdf",
    )

    fake_repo = FakeVisitReportRepository()
    fake_repo.records["report-1"] = {
        "id": "report-1",
        "organization_id": "org-1",
        "project_id": "project-1",
        "visit_date": "2025-03-15",
        "visit_type": "STRUCTURE_SITE",
        "status": "LOCKED",
        "pdf_storage_path": storage_path,
        "pdf_filename": "march.pdf",
    }

    return FieldVisitReportExportService(
        report_repository=fake_repo,
        project_repository=FakeProjectRepository(),
        organization_repository=FakeOrganizationRepository(),
        pdf_service=pdf_service,
    )


def test_admin_export_field_reports_returns_zip(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    export_service = _build_export_service(tmp_path)
    monkeypatch.setattr(
        "app.dependencies.field_visit_report_export_service",
        export_service,
    )

    client = TestClient(app)
    response = client.get(
        "/admin/field-reports/organizations/org-1/export",
        headers=_headers(_token()),
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert "attachment" in response.headers["content-disposition"]
    assert "field-reports_" in response.headers["content-disposition"]

    with zipfile.ZipFile(BytesIO(response.content)) as archive:
        names = archive.namelist()
        assert "manifest.json" in names
        assert any(name.endswith("march.pdf") for name in names)

        manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
        assert manifest["total_included"] == 1
        assert manifest["organization_name"] == "לקוח א"
        assert archive.read(
            next(name for name in names if name.endswith("march.pdf"))
        ) == FAKE_PDF


def test_non_platform_role_cannot_export_field_reports():
    client = TestClient(app)
    response = client.get(
        "/admin/field-reports/organizations/org-1/export",
        headers=_headers(_token(role="SUPERVISOR")),
    )

    assert response.status_code == 403


def test_admin_export_field_reports_returns_404_when_empty(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    export_service = FieldVisitReportExportService(
        report_repository=FakeVisitReportRepository(),
        project_repository=FakeProjectRepository(),
        organization_repository=FakeOrganizationRepository(),
        pdf_service=FieldVisitReportPdfService(
            pdfs_root=tmp_path / "field_report_pdfs"
        ),
    )
    monkeypatch.setattr(
        "app.dependencies.field_visit_report_export_service",
        export_service,
    )

    client = TestClient(app)
    response = client.get(
        "/admin/field-reports/organizations/org-1/export",
        headers=_headers(_token()),
    )

    assert response.status_code == 404
