from app.services.attachment_processor_service import (
    AttachmentProcessorService
)

from app.services.report_analysis_service import (
    ReportAnalysisService
)


pdf_service = (
    AttachmentProcessorService()
)

analysis_service = (
    ReportAnalysisService()
)

text = (
    pdf_service.extract_text_from_pdf(
        "sample_reports/weekly_report.pdf"
    )
)

result = (
    analysis_service
    .analyze_report(
        text
    )
)

print(result)