from pathlib import Path

from pypdf import PdfReader


class ReportTextExtractionService:
    MAX_PAGES = 200
    MAX_TEXT_LENGTH = 50_000

    @staticmethod
    def extract_text(
        file_path: str
    ):

        path = Path(file_path)

        if path.suffix.lower() != ".pdf":

            return ""

        try:
            reader = PdfReader(
                file_path
            )
        except Exception:
            return ""

        if getattr(reader, "is_encrypted", False):
            return ""

        extracted_text = ""

        for page in list(reader.pages)[:ReportTextExtractionService.MAX_PAGES]:

            try:
                page_text = (
                    page.extract_text()
                )
            except Exception:
                continue

            if page_text:

                extracted_text += (
                    page_text + "\n"
                )
                if len(extracted_text) >= ReportTextExtractionService.MAX_TEXT_LENGTH:
                    return extracted_text[:ReportTextExtractionService.MAX_TEXT_LENGTH]

        return extracted_text