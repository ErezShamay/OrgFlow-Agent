from PyPDF2 import PdfReader


class AttachmentProcessorService:
    def extract_text_from_pdf(
        self,
        file_path
    ):
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