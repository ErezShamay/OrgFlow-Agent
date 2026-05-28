from pathlib import Path

from app.services.report_processing_service import ReportProcessingService


def test_corrupted_file_handling_rejects_empty_file(tmp_path: Path):
    service = ReportProcessingService()
    empty_file = tmp_path / "empty.pdf"
    empty_file.write_bytes(b"")

    result = service._validate_file_integrity(str(empty_file), "empty.pdf")
    assert result["is_valid"] is False
    assert result["error_code"] == "EMPTY_FILE"


def test_corrupted_file_handling_rejects_invalid_pdf_signature(tmp_path: Path):
    service = ReportProcessingService()
    bad_pdf = tmp_path / "bad.pdf"
    bad_pdf.write_bytes(b"not-a-real-pdf")

    result = service._validate_file_integrity(str(bad_pdf), "bad.pdf")
    assert result["is_valid"] is False
    assert result["error_code"] == "CORRUPTED_PDF"


def test_corrupted_file_handling_accepts_valid_pdf_markers(tmp_path: Path):
    service = ReportProcessingService()
    good_pdf = tmp_path / "good.pdf"
    good_pdf.write_bytes(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\n%%EOF")

    result = service._validate_file_integrity(str(good_pdf), "good.pdf")
    assert result["is_valid"] is True
