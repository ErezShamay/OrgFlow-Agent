from app.services.automation_monitoring_service import (
    AutomationMonitoringService
)


class FakeAIExecutionLogRepository:

    def __init__(
        self,
        executions,
    ):

        self.executions = executions
        self.limit = None

    def get_recent_executions(
        self,
        limit=20,
    ):

        self.limit = limit

        return self.executions


def build_service(
    executions,
):

    service = AutomationMonitoringService.__new__(
        AutomationMonitoringService
    )

    service.ai_execution_log_repository = (
        FakeAIExecutionLogRepository(
            executions
        )
    )

    return service


def test_ai_execution_logs_dashboard_builds_summary_counts():

    service = build_service([
        {
            "id":
                "log-1",
            "status":
                "SUCCESS",
            "execution_type":
                "RISK_EVALUATION",
        },
        {
            "id":
                "log-2",
            "status":
                "FAILED",
            "execution_type":
                "PROJECT_PROCESSING",
            "failure_type":
                "TIMEOUT",
            "severity":
                "MEDIUM",
        },
        {
            "id":
                "log-3",
            "status":
                "LOW_CONFIDENCE",
            "execution_type":
                "AUTO_EXECUTION_SKIPPED",
        },
        {
            "id":
                "log-4",
            "status":
                "RECOVERED",
            "execution_type":
                "PROJECT_PROCESSING",
        },
    ])

    dashboard = (
        service
        .get_ai_execution_logs_dashboard()
    )

    assert (
        service
        .ai_execution_log_repository
        .limit
    ) == 100

    assert dashboard["summary"]["total"] == 4
    assert dashboard["summary"]["successful"] == 1
    assert dashboard["summary"]["failed"] == 1
    assert dashboard["summary"]["recovered"] == 1
    assert dashboard["summary"]["skipped"] == 1
    assert dashboard["summary"]["success_rate"] == 25
    assert dashboard["summary"]["classification_rate"] == 100

    assert dashboard["status_counts"]["SUCCESS"] == 1
    assert dashboard["execution_type_counts"]["PROJECT_PROCESSING"] == 2
    assert dashboard["failure_type_counts"]["TIMEOUT"] == 1
    assert dashboard["severity_counts"]["MEDIUM"] == 1


def test_ai_execution_logs_dashboard_reports_unclassified_failures():

    service = build_service([
        {
            "id":
                "log-1",
            "status":
                "FAILED",
            "execution_type":
                "PROJECT_PROCESSING",
        },
        {
            "id":
                "log-2",
            "status":
                "FAILED",
            "execution_type":
                "RISK_EVALUATION",
            "failure_type":
                "DATABASE",
        },
    ])

    dashboard = (
        service
        .get_ai_execution_logs_dashboard()
    )

    assert dashboard["summary"]["failed"] == 2
    assert dashboard["summary"]["classification_rate"] == 50
    assert dashboard["failure_type_counts"]["DATABASE"] == 1


def test_count_by_key_uses_unknown_for_missing_values():

    service = build_service([])

    counts = service.count_by_key(
        [
            {
                "status":
                    "SUCCESS"
            },
            {},
        ],
        "status",
    )

    assert counts == {
        "SUCCESS":
            1,
        "UNKNOWN":
            1,
    }
