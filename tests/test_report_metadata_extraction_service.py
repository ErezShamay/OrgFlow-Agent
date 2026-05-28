from pathlib import Path

from app.services.report_processing_service import ReportProcessingService


def test_report_metadata_extraction_from_filename_and_text(tmp_path: Path):
    service = ReportProcessingService()
    file_path = tmp_path / "weekly_week_12_2026-02-03.pdf"
    file_path.write_bytes(b"%PDF-1.4\nbody\n%%EOF")

    metadata = service._extract_report_metadata(
        filename=file_path.name,
        file_path=str(file_path),
        extracted_text="Site update created at 2026-02-03 with 3 key actions",
    )

    assert metadata["file_name"] == "weekly_week_12_2026-02-03.pdf"
    assert metadata["file_extension"] == "pdf"
    assert metadata["file_size_bytes"] > 0
    assert metadata["report_week"] == 12
    assert metadata["reported_at"] == "2026-02-03"
    assert metadata["word_count"] >= 5
    assert metadata["contains_ocr_fallback"] is False


def test_report_metadata_extraction_handles_missing_patterns(tmp_path: Path):
    service = ReportProcessingService()
    file_path = tmp_path / "report.bin"
    file_path.write_bytes(b"abc")

    metadata = service._extract_report_metadata(
        filename=file_path.name,
        file_path=str(file_path),
        extracted_text="[OCR_FALLBACK:bin] Unable to extract machine text from source document",
    )

    assert metadata["report_week"] is None
    assert metadata["reported_at"] is None
    assert metadata["contains_ocr_fallback"] is True
