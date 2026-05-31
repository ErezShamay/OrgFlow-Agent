from __future__ import annotations

from types import SimpleNamespace

import httpx
import pytest

from app.db.supabase_client import ResilientTransaction, SupabaseClient
from app.exceptions import ConflictError, DatabaseError


def test_execute_with_resilience_retries_transient_errors():
    attempts = {"count": 0}

    def flaky():
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise httpx.ReadError("[Errno 35] Resource temporarily unavailable")
        return "ok"

    result = SupabaseClient.execute_with_resilience(
        flaky,
        operation_name="test_retry",
        max_attempts=3,
        base_delay_seconds=0,
    )

    assert result == "ok"
    assert attempts["count"] == 3


def test_execute_with_resilience_raises_database_error_after_retries():
    def always_fail():
        raise httpx.ReadError("[Errno 35] Resource temporarily unavailable")

    with pytest.raises(DatabaseError) as exc_info:
        SupabaseClient.execute_with_resilience(
            always_fail,
            operation_name="test_retry_failure",
            max_attempts=2,
            base_delay_seconds=0,
        )

    assert exc_info.value.details["attempts"] == 2


def test_execute_with_resilience_does_not_retry_non_transient_errors():
    attempts = {"count": 0}

    def always_fail():
        attempts["count"] += 1
        raise ValueError("invalid input")

    with pytest.raises(ValueError):
        SupabaseClient.execute_with_resilience(
            always_fail,
            operation_name="test_no_retry",
            max_attempts=3,
            base_delay_seconds=0,
        )

    assert attempts["count"] == 1


def test_transaction_rolls_back_on_failure():
    events: list[str] = []

    tx = ResilientTransaction()
    tx.add(lambda: events.append("op1"), rollback=lambda: events.append("rb1"))
    tx.add(lambda: (_ for _ in ()).throw(RuntimeError("boom")), rollback=lambda: events.append("rb2"))

    with pytest.raises(DatabaseError):
        tx.commit()

    assert events == ["op1", "rb2", "rb1"]
    assert tx.committed is False
    assert tx.rollback_count == 2


def test_transaction_context_rolls_back_on_unhandled_error():
    events: list[str] = []
    tx = ResilientTransaction()
    tx.add(lambda: events.append("op"), rollback=lambda: events.append("rb"))

    with pytest.raises(RuntimeError):
        with tx:
            raise RuntimeError("explode")

    assert events == ["rb"]


def test_optimistic_update_raises_conflict_when_version_mismatch(monkeypatch: pytest.MonkeyPatch):
    class Query:
        def update(self, _):
            return self

        def eq(self, *_):
            return self

        def execute(self):
            return SimpleNamespace(data=[])

    class FakeClient:
        def table(self, _):
            return Query()

    monkeypatch.setattr("app.db.supabase_client.supabase", FakeClient())

    with pytest.raises(ConflictError):
        SupabaseClient.optimistic_update(
            table="projects",
            resource_id="p-1",
            expected_version=3,
            payload={"name": "new"},
        )
