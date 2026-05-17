from app.agent.orchestrator import Orchestrator


def test_check_missing_reports_workflow():
    orchestrator = Orchestrator()

    result = orchestrator.run("בדוק איזה פרויקטים חסרים דוח השבוע")

    assert result["status"] == "SUCCESS"
    assert len(result["missing_projects"]) == 1
    assert result["missing_projects"][0]["project_name"] == "גני השרון"


def test_send_reminders_waiting_for_confirmation():
    orchestrator = Orchestrator()

    result = orchestrator.run(
        "בדוק איזה פרויקטים חסרים דוח השבוע ושלח תזכורת למפקחים"
    )

    assert result["status"] == "WAITING_FOR_CONFIRMATION"
    assert result["confirmation_required"] is True
    assert "run_id" in result


def test_find_report_workflow():
    orchestrator = Orchestrator()

    result = orchestrator.run(
        "מצא לי את הדוח האחרון של פרויקט מגדלי צפון"
    )

    assert result["status"] == "SUCCESS"
    assert result["project"]["project_name"] == "מגדלי הצפון"


def test_summary_workflow():
    orchestrator = Orchestrator()

    result = orchestrator.run(
        "סכם לי את הסטטוס של פרויקט מגדלי הצפון"
    )

    assert result["status"] == "SUCCESS"
    assert result["project"]["project_name"] == "מגדלי הצפון"

def test_llm_fallback_find_report_workflow():
    orchestrator = Orchestrator()

    result = orchestrator.run(
        "אני צריך את הדוח של פרויקט מגדלי הצפון"
    )

    assert result["status"] == "SUCCESS"
    assert result["project"]["project_name"] == "מגדלי הצפון"
    assert result["intent_result"]["source"] == "LLM_MOCK"

def test_llm_entity_extraction_fallback():
    orchestrator = Orchestrator()

    result = orchestrator.run(
        "אני צריך את הדוח של מגדלי הצפון"
    )

    assert result["status"] == "SUCCESS"
    assert result["project"]["project_name"] == "מגדלי הצפון"
    assert result["intent_result"]["source"] == "LLM_MOCK"