from app.services.finding_extraction_service import (
    FindingExtractionService,
)


def test_extract_schedule_delay_finding():

    service = FindingExtractionService()

    text = """
    קיים עיכוב בקבלת אישור כיבוי אש.
    עבודות החשמל הושלמו.
    """

    findings = service.extract_findings(
        report_text=text,
        report_id="report-1",
        project_id="project-1",
    )

    assert len(findings) == 1

    finding = findings[0]

    assert finding.finding_type == "schedule_delay"
    assert finding.severity == "medium"