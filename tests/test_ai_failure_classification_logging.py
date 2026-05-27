from app.services.ai_automation_service import (
    AIAutomationService
)

from app.services.ai_failure_classification_service import (
    AIFailureClassificationService
)


class FakeExecutionLogRepository:

    def __init__(
        self,
    ):

        self.logs = []

    def create_log(
        self,
        log,
    ):

        self.logs.append(
            log
        )


def build_service():

    service = (
        AIAutomationService.__new__(
            AIAutomationService
        )
    )

    service.execution_log_repository = (
        FakeExecutionLogRepository()
    )

    service.ai_failure_classification_service = (
        AIFailureClassificationService()
    )

    return service


def test_failed_ai_execution_gets_failure_classification():

    service = (
        build_service()
    )

    service.log_ai_execution(

        project_id="project-1",

        execution_type="PROJECT_PROCESSING",

        status="FAILED",

        details={
            "error":
                "Request timed out"
        },

        error=TimeoutError(
            "Request timed out"
        ),
    )

    log = (
        service
        .execution_log_repository
        .logs[0]
    )

    assert log.failure_type == "TIMEOUT"
    assert log.severity == "MEDIUM"
    assert log.replayable is True


def test_failed_ai_execution_without_error_still_gets_classification():

    service = (
        build_service()
    )

    service.log_ai_execution(

        project_id="project-1",

        execution_type="PROJECT_PROCESSING",

        status="FAILED",

        details={
            "error":
                "Permission denied"
        },
    )

    log = (
        service
        .execution_log_repository
        .logs[0]
    )

    assert log.failure_type == "PERMISSION"
    assert log.severity == "HIGH"
    assert log.replayable is False


def test_successful_ai_execution_does_not_get_failure_classification():

    service = (
        build_service()
    )

    service.log_ai_execution(

        project_id="project-1",

        execution_type="RISK_EVALUATION",

        status="SUCCESS",
    )

    log = (
        service
        .execution_log_repository
        .logs[0]
    )

    assert log.failure_type is None
    assert log.severity is None
    assert log.replayable is True
