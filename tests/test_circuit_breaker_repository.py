from postgrest.exceptions import APIError

from app.repositories.circuit_breaker_repository import (
    CircuitBreakerRepository,
    _is_missing_column_error,
    _strip_optional_columns,
)


def test_strip_optional_columns():
    payload = {
        "state": "HALF_OPEN",
        "half_open_success_count": 0,
        "failure_count": 1,
    }
    assert _strip_optional_columns(payload) == {
        "state": "HALF_OPEN",
        "failure_count": 1,
    }


def test_is_missing_column_error():
    error = APIError({
        "message": "Could not find the 'half_open_success_count' column",
        "code": "PGRST204",
    })
    assert _is_missing_column_error(error, "half_open_success_count")
    assert not _is_missing_column_error(error, "other_column")


def test_update_breaker_retries_without_optional_column(monkeypatch):
    repository = CircuitBreakerRepository()
    calls: list[dict] = []

    class FakeQuery:
        def update(self, data):
            calls.append(dict(data))
            return self

        def eq(self, *_args, **_kwargs):
            return self

        def execute(self):
            if "half_open_success_count" in calls[-1]:
                raise APIError({
                    "message": "Could not find the 'half_open_success_count' column",
                    "code": "PGRST204",
                })

    class FakeClient:
        def table(self, _name):
            return FakeQuery()

    monkeypatch.setattr(repository, "client", FakeClient())

    repository.update_breaker(
        "automation:ai_recovery",
        {"state": "HALF_OPEN", "half_open_success_count": 0},
    )

    assert calls[0]["half_open_success_count"] == 0
    assert calls[1] == {"state": "HALF_OPEN"}
    assert repository.supports_half_open_success_count() is False
