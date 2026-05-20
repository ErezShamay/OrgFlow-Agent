from app.services.attachment_processor_service import (
    AttachmentProcessorService
)


service = (
    AttachmentProcessorService()
)

text = (
    service.extract_text_from_pdf(
        "sample_reports/weekly_report.pdf"
    )
)

print(text)
