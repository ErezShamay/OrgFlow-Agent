from app.services.report_ingestion_service import ReportIngestionService


def test_process_message_returns_success_for_matching_project():
    ingestion_service = ReportIngestionService()
    ingestion_service.project_tool.get_active_projects = lambda: [
        {"project_name": "Alpha", "status": "ACTIVE"},
        {"project_name": "Beta", "status": "ACTIVE"},
    ]

    message = {"subject": "Update for Alpha"}

    result = ingestion_service.process_message(message)

    assert result["status"] == "SUCCESS"
    assert result["project"]["project_name"] == "Alpha"
    assert result["message"] == message


def test_process_message_returns_no_project_match_for_unknown_subject():
    ingestion_service = ReportIngestionService()
    ingestion_service.project_tool.get_active_projects = lambda: [
        {"project_name": "Alpha", "status": "ACTIVE"},
    ]

    message = {"subject": "Update for Gamma"}

    result = ingestion_service.process_message(message)

    assert result["status"] == "NO_PROJECT_MATCH"
