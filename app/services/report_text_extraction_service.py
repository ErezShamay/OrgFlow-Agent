from pathlib import Path

from PyPDF2 import PdfReader


class ReportTextExtractionService:

    @staticmethod
    def extract_text(
        file_path: str
    ):

        path = Path(file_path)

        if path.suffix.lower() != ".pdf":

            return ""

        reader = PdfReader(
            file_path
        )

        extracted_text = ""

        for page in reader.pages:

            page_text = (
                page.extract_text()
            )

            if page_text:

                extracted_text += (
                    page_text + "\n"
                )

        return extracted_text