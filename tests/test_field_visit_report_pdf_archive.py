from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.services.field_report_module_service import (
    FieldReportModuleService,
)
from app.services.field_report_organization_profile_service import (
    FieldReportOrganizationProfileService,
)
from app.services.field_visit_report_archive_service import (
    build_project_field_report_archive,
)
from app.services.field_visit_report_pdf_service import (
    FieldVisitReportPdfService,
)
from app.services.field_visit_report_service import (
    FieldVisitReportService,
)
from tests.test_field_visit_reports import (
    FakeProjectRepository,
    FakeReportProcessingService,
    FakeVisitReportLinePhotoRepository,
    FakeVisitReportLineRepository,
    FakeVisitReportRepository,
)

FAKE_PDF = b"%PDF-1.4\narchived-report\n%%EOF\n"


def test_pdf_service_saves_and_reads_pdf(tmp_path: Path):
    service = FieldVisitReportPdfService(pdfs_root=tmp_path / "pdfs")

    storage_path, filename = service.save_pdf(
        organization_id="org-1",
        project_id="project-1",
        report_id="report-1",
        content=FAKE_PDF,
        filename="visit-report.pdf",
    )

    assert filename.endswith(".pdf")
    assert storage_path.startswith("org-1/project-1/report-1/")

    content, content_type = service.read_pdf(storage_path)
    assert content == FAKE_PDF
    assert content_type == "application/pdf"


def test_pdf_service_rejects_invalid_pdf(tmp_path: Path):
    service = FieldVisitReportPdfService(pdfs_root=tmp_path / "pdfs")

    with pytest.raises(Exception):
        service.save_pdf(
            organization_id="org-1",
            project_id="project-1",
            report_id="report-1",
            content=b"not-a-pdf",
            filename="bad.pdf",
        )


def test_build_project_field_report_archive_groups_by_year_and_month():
    archive = build_project_field_report_archive(
        [
            {
                "id": "r1",
                "visit_date": "2025-03-15",
                "visit_type": "STRUCTURE_SITE",
                "pdf_storage_path": "org/p/r1/a.pdf",
                "pdf_filename": "march.pdf",
                "locked_at": "2025-03-16T10:00:00+00:00",
            },
            {
                "id": "r2",
                "visit_date": "2026-06-01",
                "visit_type": "MIXED",
                "pdf_storage_path": "org/p/r2/b.pdf",
                "pdf_filename": "june.pdf",
                "locked_at": "2026-06-02T10:00:00+00:00",
            },
            {
                "id": "r3",
                "visit_date": "2026-06-20",
                "visit_type": "FINISHING_APARTMENTS",
                "pdf_storage_path": "org/p/r3/c.pdf",
                "pdf_filename": "june-2.pdf",
                "locked_at": "2026-06-21T10:00:00+00:00",
            },
        ],
        project_id="project-1",
        project_name="פרויקט",
    )

    assert archive["total_reports"] == 3
    assert [year["year"] for year in archive["years"]] == [2026, 2025]
    assert archive["years"][0]["months"][0]["month"] == 6
    assert len(archive["years"][0]["months"][0]["reports"]) == 2
    assert archive["years"][1]["months"][0]["month_label_he"] == "מרץ"


def test_request_send_archives_pdf_for_project_archive(tmp_path: Path):
    from app.services.field_visit_report_core_adapter import (
        FieldVisitReportCoreAdapter,
    )

    fake_processing = FakeReportProcessingService()
    fake_repo = FakeVisitReportRepository()
    pdf_service = FieldVisitReportPdfService(
        pdfs_root=tmp_path / "field_report_pdfs"
    )

    service = FieldVisitReportService(
        report_repository=fake_repo,
        line_repository=FakeVisitReportLineRepository(),
        line_photo_repository=FakeVisitReportLinePhotoRepository(),
        project_repository=FakeProjectRepository(),
        pdf_service=pdf_service,
        core_adapter=FieldVisitReportCoreAdapter(
            report_processing_service=fake_processing,
        ),
    )

    created = fake_repo.create(
        organization_id="org-1",
        project_id="project-1",
        created_by_profile_id="supervisor-1",
        visit_type="STRUCTURE_SITE",
        visit_date="2026-06-01",
        header_fields={},
    )
    report_id = created["id"]
    fake_repo.update(
        report_id,
        {
            "status": "CLOSED",
            "closed_at": "2026-06-01T12:00:00+00:00",
        },
    )

    locked = service.request_send_to_core(
        organization_id="org-1",
        report_id=report_id,
        source_filename=f"{report_id}.pdf",
        source_content=FAKE_PDF,
    )

    assert locked["status"] == "LOCKED"
    assert locked["has_archived_pdf"] is True
    assert locked["pdf_filename"]

    stored = fake_repo.get_by_id(report_id)
    assert stored["pdf_storage_path"]
    content, _ = pdf_service.read_pdf(stored["pdf_storage_path"])
    assert content == FAKE_PDF

    archive = service.get_project_field_report_archive(
        organization_id="org-1",
        project_id="project-1",
    )
    assert archive["total_reports"] == 1
    assert archive["years"][0]["year"] == 2026
    assert archive["years"][0]["months"][0]["month"] == 6

    pdf_bytes, _, filename = service.get_archived_report_pdf(
        organization_id="org-1",
        report_id=report_id,
    )
    assert pdf_bytes == FAKE_PDF
    assert filename.endswith(".pdf")
