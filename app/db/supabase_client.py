from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from contextlib import AbstractContextManager
import threading
import time
from collections.abc import Callable
from typing import Any

from supabase import create_client

from app.config.settings import settings
from app.exceptions import ConflictError, DatabaseError


SUPABASE_URL = str(settings.SUPABASE_URL) if settings.SUPABASE_URL else None
SUPABASE_KEY = str(settings.SUPABASE_KEY) if settings.SUPABASE_KEY else None

if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase = None


def _run_with_timeout(
    operation: Callable[[], Any],
    timeout_seconds: float,
) -> Any:
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(operation)
        try:
            return future.result(timeout=timeout_seconds)
        except FuturesTimeoutError as exc:
            raise DatabaseError(
                message="Database operation timed out",
                operation="timeout",
                details={"timeout_seconds": timeout_seconds},
            ) from exc


class ResilientTransaction(AbstractContextManager["ResilientTransaction"]):
    """
    Best-effort transactional unit for Supabase operations.
    Since not all operations can run in a DB-level SQL transaction from this layer,
    this class supports compensating rollbacks on failure.
    """

    def __init__(self) -> None:
        self._operations: list[Callable[[], Any]] = []
        self._rollbacks: list[Callable[[], Any]] = []
        self._executed_rollbacks: list[Callable[[], Any]] = []
        self._committed = False

    def add(
        self,
        operation: Callable[[], Any],
        rollback: Callable[[], Any] | None = None,
    ) -> None:
        self._operations.append(operation)
        if rollback is not None:
            self._rollbacks.append(rollback)

    @property
    def committed(self) -> bool:
        return self._committed

    @property
    def rollback_count(self) -> int:
        return len(self._executed_rollbacks)

    def commit(self) -> None:
        committed_ops = 0
        try:
            for operation in self._operations:
                SupabaseClient.execute_with_resilience(operation, operation_name="transaction_commit")
                committed_ops += 1
            self._committed = True
        except Exception as exc:
            self._rollback()
            raise DatabaseError(
                message="Transaction failed and was rolled back",
                operation="transaction_commit",
                details={"committed_operations": committed_ops},
            ) from exc

    def _rollback(self) -> None:
        for rollback in reversed(self._rollbacks):
            try:
                rollback()
            finally:
                self._executed_rollbacks.append(rollback)

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc is not None and not self._committed:
            self._rollback()
        return None


class SupabaseClient:
    _update_locks: dict[str, threading.Lock] = {}
    _update_locks_guard = threading.Lock()

    @staticmethod
    def get_client():
        if supabase is None:
            raise DatabaseError(
                message="Supabase is not configured",
                operation="get_client",
            )
        return supabase

    @classmethod
    def _get_update_lock(cls, key: str) -> threading.Lock:
        with cls._update_locks_guard:
            if key not in cls._update_locks:
                cls._update_locks[key] = threading.Lock()
            return cls._update_locks[key]

    @staticmethod
    def execute_with_resilience(
        operation: Callable[[], Any],
        *,
        operation_name: str = "db_operation",
        max_attempts: int | None = None,
        timeout_seconds: float | None = None,
        base_delay_seconds: float | None = None,
    ) -> Any:
        attempts = max_attempts or settings.DB_RETRY_MAX_ATTEMPTS
        timeout = timeout_seconds or settings.DB_OPERATION_TIMEOUT_SECONDS
        base_delay = (
            settings.DB_RETRY_BASE_DELAY_SECONDS
            if base_delay_seconds is None
            else base_delay_seconds
        )
        last_error: Exception | None = None

        for attempt in range(1, attempts + 1):
            try:
                return _run_with_timeout(operation, timeout)
            except DatabaseError:
                raise
            except Exception as exc:
                last_error = exc
                if attempt >= attempts:
                    break
                backoff = base_delay * (2 ** (attempt - 1))
                if backoff > 0:
                    time.sleep(backoff)

        raise DatabaseError(
            message="Database operation failed after retries",
            operation=operation_name,
            details={"attempts": attempts},
        ) from last_error

    @staticmethod
    def transaction() -> ResilientTransaction:
        return ResilientTransaction()

    @classmethod
    def optimistic_update(
        cls,
        *,
        table: str,
        resource_id: str,
        expected_version: int,
        payload: dict[str, Any],
        id_field: str = "id",
        version_field: str = "version",
    ) -> Any:
        lock_key = f"{table}:{resource_id}"
        resource_lock = cls._get_update_lock(lock_key)
        with resource_lock:
            update_payload = dict(payload)
            update_payload[version_field] = expected_version + 1

            def perform_update():
                return (
                    supabase.table(table)
                    .update(update_payload)
                    .eq(id_field, resource_id)
                    .eq(version_field, expected_version)
                    .execute()
                )

            response = cls.execute_with_resilience(
                perform_update,
                operation_name="optimistic_update",
            )
            if not getattr(response, "data", None):
                raise ConflictError(
                    message="Concurrent update detected",
                    details={
                        "table": table,
                        "resource_id": resource_id,
                        "expected_version": expected_version,
                    },
                )
            return response
