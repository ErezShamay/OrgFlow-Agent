from app.services.report_processing_service import ReportProcessingService


def test_report_tagging_normalizes_and_deduplicates():
    service = ReportProcessingService()
    response = service.update_report_tags("p1", "r1", ["Delay", "delay", " Safety "])
    assert response["tags"] == ["delay", "safety"]


def test_report_tagging_list_and_search():
    service = ReportProcessingService()
    service.update_report_tags("p1", "r1", ["safety", "risk"])
    service.update_report_tags("p1", "r2", ["budget"])

    assert service.list_report_tags("r1") == ["risk", "safety"]
    results = service.search_reports_by_tag("p1", "safety")
    assert results["report_ids"] == ["r1"]
    assert results["total_reports"] == 1
