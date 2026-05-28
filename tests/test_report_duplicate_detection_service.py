from app.services.report_processing_service import ReportProcessingService


class FakeReportRepository:
    def __init__(self, reports):
        self._reports = reports

    def get_reports_by_project(self, _project_id: str):
        return self._reports


def test_duplicate_detection_by_filename_lineage():
    service = ReportProcessingService()
    service.report_repository = FakeReportRepository(
        [
            {"email_subject": "weekly-report.pdf (v1)"},
        ]
    )
    service._get_existing_interpretation_previews = lambda _project_id: []

    result = service._detect_duplicate_report(
        project_id="p1",
        filename="weekly-report.pdf",
        text_preview="new content",
    )
    assert result["is_duplicate"] is True
    assert "same_filename_lineage" in result["signals"]


def test_duplicate_detection_by_matching_text_preview():
    service = ReportProcessingService()
    service.report_repository = FakeReportRepository([])
    service._get_existing_interpretation_previews = lambda _project_id: ["same preview"]

    result = service._detect_duplicate_report(
        project_id="p1",
        filename="fresh-report.pdf",
        text_preview="same preview",
    )
    assert result["is_duplicate"] is True
    assert "matching_text_preview" in result["signals"]


def test_duplicate_detection_allows_unique_report():
    service = ReportProcessingService()
    service.report_repository = FakeReportRepository(
        [
            {"email_subject": "another-file.pdf (v1)"},
        ]
    )
    service._get_existing_interpretation_previews = lambda _project_id: ["different preview"]

    result = service._detect_duplicate_report(
        project_id="p1",
        filename="weekly-report.pdf",
        text_preview="new preview",
    )
    assert result["is_duplicate"] is False
    assert result["signals"] == []
