import pytest

from app.automation import jobs


class FakeCircuitBreakerService:

    def __init__(
        self,
        allowed=True,
    ):

        self.allowed = allowed
        self.successes = []
        self.failures = []

    def allow_request(
        self,
        job_name,
    ):

        return self.allowed

    def record_success(
        self,
        job_name,
    ):

        self.successes.append(
            job_name
        )

    def record_failure(
        self,
        job_name,
    ):

        self.failures.append(
            job_name
        )


class FakeAutomationLockService:

    def __init__(
        self,
        acquired=True,
    ):

        self.acquired = acquired
        self.acquire_calls = []
        self.release_calls = []

    def acquire_lock(
        self,
        job_name,
    ):

        self.acquire_calls.append(
            job_name
        )

        return self.acquired

    def release_lock(
        self,
        job_name,
    ):

        self.release_calls.append(
            job_name
        )


class FakeAutomationRunService:

    def __init__(
        self,
    ):

        self.started = []
        self.completed = []
        self.failed = []
        self.skipped = []

    def start_run(
        self,
        job_name,
        metadata=None,
    ):

        self.started.append(
            {
                "job_name":
                    job_name,
                "metadata":
                    metadata,
            }
        )

        return "run-1"

    def complete_run(
        self,
        run_id,
        processed_count=0,
        error_count=0,
        metadata=None,
    ):

        self.completed.append(
            {
                "run_id":
                    run_id,
                "processed_count":
                    processed_count,
                "error_count":
                    error_count,
                "metadata":
                    metadata,
            }
        )

    def fail_run(
        self,
        run_id,
        error,
        metadata=None,
    ):

        self.failed.append(
            {
                "run_id":
                    run_id,
                "error":
                    str(error),
                "metadata":
                    metadata,
            }
        )

    def skip_run(
        self,
        job_name,
        reason,
        metadata=None,
    ):

        self.skipped.append(
            {
                "job_name":
                    job_name,
                "reason":
                    reason,
                "metadata":
                    metadata,
            }
        )


@pytest.fixture
def fake_services(
    monkeypatch,
):

    circuit_breaker = (
        FakeCircuitBreakerService()
    )

    lock_service = (
        FakeAutomationLockService()
    )

    run_service = (
        FakeAutomationRunService()
    )

    monkeypatch.setattr(
        jobs,
        "circuit_breaker_service",
        circuit_breaker,
    )

    monkeypatch.setattr(
        jobs,
        "automation_lock_service",
        lock_service,
    )

    monkeypatch.setattr(
        jobs,
        "automation_run_service",
        run_service,
    )

    return {
        "circuit_breaker":
            circuit_breaker,
        "lock_service":
            lock_service,
        "run_service":
            run_service,
    }


def test_run_automation_job_records_completed_run(
    fake_services,
):

    jobs.run_automation_job(

        job_name="demo_job",

        log_prefix="TEST",

        handler=lambda: {
            "processed_count":
                3,
            "error_count":
                0,
            "metadata":
                {
                    "batch_size":
                        3
                },
        },
    )

    run_service = (
        fake_services["run_service"]
    )

    assert run_service.started[0]["job_name"] == "demo_job"
    assert run_service.completed[0]["run_id"] == "run-1"
    assert run_service.completed[0]["processed_count"] == 3
    assert run_service.completed[0]["metadata"]["job_type"] == "DEMO_JOB"
    assert fake_services["circuit_breaker"].successes == ["demo_job"]
    assert fake_services["lock_service"].release_calls == ["demo_job"]


def test_run_automation_job_records_circuit_breaker_skip(
    fake_services,
):

    fake_services["circuit_breaker"].allowed = False

    jobs.run_automation_job(

        job_name="demo_job",

        log_prefix="TEST",

        handler=lambda: {},
    )

    run_service = (
        fake_services["run_service"]
    )

    assert run_service.skipped[0]["reason"] == "CIRCUIT_BREAKER_OPEN"
    assert fake_services["lock_service"].acquire_calls == []
    assert run_service.started == []


def test_run_automation_job_records_lock_skip(
    fake_services,
):

    fake_services["lock_service"].acquired = False

    jobs.run_automation_job(

        job_name="demo_job",

        log_prefix="TEST",

        handler=lambda: {},
    )

    run_service = (
        fake_services["run_service"]
    )

    assert run_service.skipped[0]["reason"] == "LOCK_NOT_ACQUIRED"
    assert run_service.started == []
    assert fake_services["lock_service"].release_calls == []


def test_run_automation_job_records_failed_run(
    fake_services,
):

    def failing_handler():

        raise RuntimeError(
            "boom"
        )

    jobs.run_automation_job(

        job_name="demo_job",

        log_prefix="TEST",

        handler=failing_handler,
    )

    run_service = (
        fake_services["run_service"]
    )

    assert run_service.failed[0]["run_id"] == "run-1"
    assert run_service.failed[0]["error"] == "boom"
    assert fake_services["circuit_breaker"].failures == ["demo_job"]
    assert fake_services["lock_service"].release_calls == ["demo_job"]
