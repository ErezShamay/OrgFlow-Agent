from app.services.report_processing_service import ReportProcessingService


def test_report_indexing_builds_tokens():
    service = ReportProcessingService()
    service.report_tags["r1"] = ["safety", "delay"]

    entry = service.index_report(
        project_id="p1",
        report_id="r1",
        filename="weekly-report.pdf",
        classification={"category": "DELAY", "signals": ["delay"]},
        metadata={"file_extension": "pdf", "report_week": 12},
        ai_insights={"sentiment": "negative", "summary": "delay flagged in execution"},
    )

    assert entry["report_id"] == "r1"
    assert "delay" in entry["tokens"]
    assert "weekly-report" in entry["tokens"] or "weekly" in entry["tokens"]


def test_report_indexing_list_project_entries():
    service = ReportProcessingService()
    service.report_index = {
        "r1": {"project_id": "p1", "report_id": "r1", "indexed_at": "2026-01-01T00:00:00Z"},
        "r2": {"project_id": "p2", "report_id": "r2", "indexed_at": "2026-01-01T00:00:00Z"},
    }

    payload = service.list_project_index_entries("p1")
    assert payload["total_indexed_reports"] == 1
    assert payload["entries"][0]["report_id"] == "r1"
