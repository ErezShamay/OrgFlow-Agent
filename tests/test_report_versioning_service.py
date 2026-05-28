from app.services.report_processing_service import ReportProcessingService


class FakeReportRepository:
    def __init__(self, reports):
        self._reports = reports

    def get_reports_by_project(self, _project_id: str):
        return self._reports


def test_report_versioning_first_upload_gets_v1():
    service = ReportProcessingService()
    service.report_repository = FakeReportRepository([])

    subject, version = service._build_versioned_subject("p1", "weekly-report.pdf")
    assert subject == "weekly-report.pdf (v1)"
    assert version == 1


def test_report_versioning_increments_for_same_file_name():
    service = ReportProcessingService()
    service.report_repository = FakeReportRepository(
        [
            {"email_subject": "weekly-report.pdf (v1)"},
            {"email_subject": "weekly-report.pdf (v2)"},
            {"email_subject": "other-report.pdf (v4)"},
        ]
    )

    subject, version = service._build_versioned_subject("p1", "weekly-report.pdf")
    assert subject == "weekly-report.pdf (v3)"
    assert version == 3


def test_report_versioning_matches_case_insensitive():
    service = ReportProcessingService()
    service.report_repository = FakeReportRepository(
        [
            {"email_subject": "Weekly-Report.PDF (v2)"},
        ]
    )

    subject, version = service._build_versioned_subject("p1", "weekly-report.pdf")
    assert subject == "weekly-report.pdf (v3)"
    assert version == 3


def test_report_versioning_handles_legacy_subject_without_suffix():
    service = ReportProcessingService()
    base, version = service._parse_versioned_subject("legacy-report.pdf")
    assert base == "legacy-report.pdf"
    assert version == 1
