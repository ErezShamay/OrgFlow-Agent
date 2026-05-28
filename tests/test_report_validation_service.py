from app.services.report_processing_service import ReportProcessingService


def test_report_validation_accepts_valid_attachment_payload():
    service = ReportProcessingService()
    result = service.validate_attachment_payload(
        report_id="r1",
        filename="annex.xlsx",
        uploaded_by="dana",
    )
    assert result["is_valid"] is True


def test_report_validation_rejects_invalid_attachment_type():
    service = ReportProcessingService()
    result = service.validate_attachment_payload(
        report_id="r1",
        filename="payload.exe",
        uploaded_by="dana",
    )
    assert result["is_valid"] is False
    assert result["error_code"] == "UNSUPPORTED_ATTACHMENT_TYPE"


def test_report_validation_rejects_empty_uploader():
    service = ReportProcessingService()
    result = service.validate_attachment_payload(
        report_id="r1",
        filename="payload.pdf",
        uploaded_by=" ",
    )
    assert result["is_valid"] is False
    assert result["error_code"] == "INVALID_UPLOADER"
