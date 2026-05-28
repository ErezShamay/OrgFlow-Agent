from app.services.report_text_extraction_service import ReportTextExtractionService
import app.services.report_text_extraction_service as extraction_module


class FakePage:
    def __init__(self, text: str | None = None, fail: bool = False):
        self._text = text
        self._fail = fail

    def extract_text(self):
        if self._fail:
            raise ValueError("page parse error")
        return self._text


class FakeReader:
    def __init__(self, pages, is_encrypted=False):
        self.pages = pages
        self.is_encrypted = is_encrypted


def test_pdf_parser_hardening_non_pdf_returns_empty():
    result = ReportTextExtractionService.extract_text("report.txt")
    assert result == ""


def test_pdf_parser_hardening_reader_init_failure(monkeypatch):
    def _broken_reader(_):
        raise RuntimeError("bad pdf")

    monkeypatch.setattr(extraction_module, "PdfReader", _broken_reader)
    result = ReportTextExtractionService.extract_text("broken.pdf")
    assert result == ""


def test_pdf_parser_hardening_encrypted_pdf(monkeypatch):
    monkeypatch.setattr(
        extraction_module,
        "PdfReader",
        lambda _: FakeReader([], is_encrypted=True),
    )
    result = ReportTextExtractionService.extract_text("secret.pdf")
    assert result == ""


def test_pdf_parser_hardening_skip_failing_pages(monkeypatch):
    monkeypatch.setattr(
        extraction_module,
        "PdfReader",
        lambda _: FakeReader(
            [
                FakePage(text="first page"),
                FakePage(fail=True),
                FakePage(text="third page"),
            ]
        ),
    )
    result = ReportTextExtractionService.extract_text("mixed.pdf")
    assert "first page" in result
    assert "third page" in result


def test_pdf_parser_hardening_text_limit(monkeypatch):
    original_limit = ReportTextExtractionService.MAX_TEXT_LENGTH
    ReportTextExtractionService.MAX_TEXT_LENGTH = 20

    try:
        monkeypatch.setattr(
            extraction_module,
            "PdfReader",
            lambda _: FakeReader([FakePage(text="abcdefghijklmnopqrstuvwxyz")]),
        )
        result = ReportTextExtractionService.extract_text("large.pdf")
        assert len(result) == 20
    finally:
        ReportTextExtractionService.MAX_TEXT_LENGTH = original_limit
