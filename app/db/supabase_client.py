from __future__ import annotations

from contextlib import AbstractContextManager
import os
import ssl
import threading
import time
from collections.abc import Callable
from typing import Any

import httpx
from supabase import create_client
from supabase.lib.client_options import SyncClientOptions

from app.config.settings import settings
from app.exceptions import ConflictError, DatabaseError


SUPABASE_URL = str(settings.SUPABASE_URL) if settings.SUPABASE_URL else None
SUPABASE_KEY = str(settings.SUPABASE_KEY) if settings.SUPABASE_KEY else None

_TRANSIENT_ERRNOS = frozenset({11, 35, 104, 110})
_TRANSIENT_EXCEPTIONS = (
    httpx.ReadError,
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
    httpx.PoolTimeout,
    httpx.RemoteProtocolError,
    httpx.NetworkError,
)


def _is_transient_error(exc: Exception) -> bool:
    if isinstance(exc, _TRANSIENT_EXCEPTIONS):
        return True

    cause = exc.__cause__
    if isinstance(cause, OSError) and cause.errno in _TRANSIENT_ERRNOS:
        return True

    message = str(exc).lower()
    return "resource temporarily unavailable" in message


def _build_ssl_context() -> ssl.SSLContext:
    """Use the OS trust store (corporate roots on Windows, Keychain on macOS)."""
    for env_var in ("SSL_CERT_FILE", "REQUESTS_CA_BUNDLE"):
        path = os.environ.get(env_var)
        if path and os.path.isfile(path):
            context = ssl.create_default_context(cafile=path)
            return context
    return ssl.create_default_context()


def _build_httpx_client() -> httpx.Client:
    timeout = httpx.Timeout(settings.DB_OPERATION_TIMEOUT_SECONDS)
    limits = httpx.Limits(
        max_connections=20,
        max_keepalive_connections=10,
    )
    return httpx.Client(
        timeout=timeout,
        limits=limits,
        verify=_build_ssl_context(),
        trust_env=False,
    )


class ResilientRequestBuilder:
    __slots__ = ("_builder",)

    def __init__(self, builder: Any) -> None:
        object.__setattr__(self, "_builder", builder)

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        return SupabaseClient.execute_with_resilience(
            lambda: self._builder.execute(*args, **kwargs),
            operation_name="postgrest_execute",
        )

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self._builder, name)
        if not callable(attr):
            return attr

        def method(*args: Any, **kwargs: Any) -> Any:
            result = attr(*args, **kwargs)
            if hasattr(result, "execute"):
                return ResilientRequestBuilder(result)
            return result

        return method


class ResilientAuthAdminProxy:
    __slots__ = ("_admin",)

    def __init__(self, admin: Any) -> None:
        object.__setattr__(self, "_admin", admin)

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self._admin, name)
        if not callable(attr):
            return attr

        def method(*args: Any, **kwargs: Any) -> Any:
            return SupabaseClient.execute_with_resilience(
                lambda: attr(*args, **kwargs),
                operation_name=f"auth_admin_{name}",
            )

        return method


class ResilientAuthProxy:
    __slots__ = ("_auth",)

    def __init__(self, auth: Any) -> None:
        object.__setattr__(self, "_auth", auth)

    @property
    def admin(self) -> ResilientAuthAdminProxy:
        return ResilientAuthAdminProxy(self._auth.admin)

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self._auth, name)
        if not callable(attr):
            return attr

        def method(*args: Any, **kwargs: Any) -> Any:
            return SupabaseClient.execute_with_resilience(
                lambda: attr(*args, **kwargs),
                operation_name=f"auth_{name}",
            )

        return method


class ResilientSupabaseProxy:
    __slots__ = ("_client",)

    def __init__(self, client: Any) -> None:
        object.__setattr__(self, "_client", client)

    def table(self, name: str) -> ResilientRequestBuilder:
        return ResilientRequestBuilder(self._client.table(name))

    @property
    def auth(self) -> ResilientAuthProxy:
        return ResilientAuthProxy(self._client.auth)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)


def _create_supabase_client() -> ResilientSupabaseProxy | None:
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None

    options = SyncClientOptions(
        httpx_client=_build_httpx_client(),
    )
    client = create_client(SUPABASE_URL, SUPABASE_KEY, options)
    return ResilientSupabaseProxy(client)


supabase = _create_supabase_client()


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
                SupabaseClient.execute_with_resilience(
                    operation,
                    operation_name="transaction_commit",
                )
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
        base_delay_seconds: float | None = None,
    ) -> Any:
        attempts = max_attempts or settings.DB_RETRY_MAX_ATTEMPTS
        base_delay = (
            settings.DB_RETRY_BASE_DELAY_SECONDS
            if base_delay_seconds is None
            else base_delay_seconds
        )
        last_error: Exception | None = None

        for attempt in range(1, attempts + 1):
            try:
                return operation()
            except DatabaseError:
                raise
            except Exception as exc:
                last_error = exc
                should_retry = _is_transient_error(exc)
                if not should_retry or attempt >= attempts:
                    break
                backoff = base_delay * (2 ** (attempt - 1))
                if backoff > 0:
                    time.sleep(backoff)

        if isinstance(last_error, Exception) and not _is_transient_error(
            last_error
        ):
            raise last_error

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
