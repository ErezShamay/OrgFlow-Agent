from app.repositories.ai_execution_log_repository import (
    AIExecutionLogRepository
)

from app.services.ai_recovery_service import (
    AIRecoveryService
)


class FakeQuery:

    def __init__(
        self,
    ):

        self.payload = None
        self.filters = []

    def select(
        self,
        value,
    ):

        return self

    def update(
        self,
        payload,
    ):

        self.payload = payload

        return self

    def eq(
        self,
        key,
        value,
    ):

        self.filters.append(
            (
                key,
                value,
            )
        )

        return self

    def lt(
        self,
        key,
        value,
    ):

        self.filters.append(
            (
                key,
                value,
            )
        )

        return self

    def or_(
        self,
        value,
    ):

        self.filters.append(
            (
                "or",
                value,
            )
        )

        return self

    def order(
        self,
        key,
        desc=False,
    ):

        return self

    def execute(
        self,
    ):

        return type(
            "Response",
            (),
            {
                "data":
                    []
            },
        )()


class FakeClient:

    def __init__(
        self,
    ):

        self.query = FakeQuery()

    def table(
        self,
        table_name,
    ):

        return self.query


class FakeRecoveryRepository:

    def __init__(
        self,
    ):

        self.locked = []
        self.unlocked = []
        self.updated_retries = []
        self.dead_letters = []

    def lock_recovery(
        self,
        log_id,
    ):

        self.locked.append(
            log_id
        )

    def unlock_recovery(
        self,
        log_id,
    ):

        self.unlocked.append(
            log_id
        )

    def update_retry(
        self,
        log_id,
        retry_count,
        next_retry_at,
    ):

        self.updated_retries.append(
            log_id
        )

    def mark_dead_letter(
        self,
        log_id,
    ):

        self.dead_letters.append(
            log_id
        )


def build_repository_with_fake_client():

    repository = (
        AIExecutionLogRepository.__new__(
            AIExecutionLogRepository
        )
    )

    client = FakeClient()

    repository.client = client
    repository.table_name = "ai_execution_logs"

    return repository, client


def test_get_failed_executions_excludes_dead_letters():

    repository, client = (
        build_repository_with_fake_client()
    )

    repository.get_failed_executions()

    assert (
        "dead_lettered",
        False,
    ) in client.query.filters


def test_mark_dead_letter_preserves_record_and_removes_from_retry_flow():

    repository, client = (
        build_repository_with_fake_client()
    )

    repository.mark_dead_letter(
        "log-1"
    )

    assert client.query.payload == {
        "status":
            "DEAD_LETTERED",
        "dead_lettered":
            True,
        "recovery_locked":
            False,
        "next_retry_at":
            None,
    }

    assert (
        "id",
        "log-1",
    ) in client.query.filters


def test_retry_execution_skips_existing_dead_letter():

    service = (
        AIRecoveryService.__new__(
            AIRecoveryService
        )
    )

    repository = (
        FakeRecoveryRepository()
    )

    service.repository = repository

    service.retry_execution(
        {
            "id":
                "log-1",
            "dead_lettered":
                True,
            "retry_count":
                3,
        }
    )

    assert repository.locked == []
    assert repository.unlocked == []
    assert repository.updated_retries == []
    assert repository.dead_letters == []
