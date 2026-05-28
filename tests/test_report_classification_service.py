from app.services.report_processing_service import ReportProcessingService


def test_report_classification_detects_safety_keywords():
    service = ReportProcessingService()
    classification = service._classify_report(
        filename="weekly-safety-report.pdf",
        extracted_text="Incident found in site hazard area",
    )
    assert classification["category"] == "SAFETY"
    assert classification["confidence"] >= 0.55
    assert "hazard" in classification["signals"] or "incident" in classification["signals"]


def test_report_classification_detects_budget_keywords():
    service = ReportProcessingService()
    classification = service._classify_report(
        filename="finance.pdf",
        extracted_text="Budget overrun due to vendor invoice increase",
    )
    assert classification["category"] == "BUDGET"
    assert classification["recommended_action"].startswith("Validate budget variance")


def test_report_classification_defaults_to_general():
    service = ReportProcessingService()
    classification = service._classify_report(
        filename="notes.pdf",
        extracted_text="Routine weekly update with no major exceptions",
    )
    assert classification["category"] == "GENERAL"
    assert classification["confidence"] == 0.45
