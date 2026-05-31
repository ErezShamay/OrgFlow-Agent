from postgrest.exceptions import APIError

from app.db.supabase_client import (
    supabase
)

from app.schemas.circuit_breaker import (
    CircuitBreaker
)

_OPTIONAL_COLUMNS = frozenset({"half_open_success_count"})


def _strip_optional_columns(data: dict) -> dict:
    return {
        key: value
        for key, value in data.items()
        if key not in _OPTIONAL_COLUMNS
    }


def _is_missing_column_error(
    error: APIError,
    column: str,
) -> bool:
    code = getattr(error, "code", None)
    message = str(getattr(error, "message", error))
    return code == "PGRST204" and column in message


class CircuitBreakerRepository:

    def __init__(self):

        self.client = (
            supabase
        )

        self.table_name = (
            "circuit_breakers"
        )

        self._supports_half_open_success_count: bool | None = None

    def supports_half_open_success_count(self) -> bool:
        if self._supports_half_open_success_count is None:
            return True
        return self._supports_half_open_success_count

    def _mark_half_open_column_unsupported(self) -> None:
        self._supports_half_open_success_count = False

    def _run_update(
        self,
        breaker_key: str,
        data: dict,
    ) -> None:
        (
            self.client
            .table(self.table_name)
            .update(data)
            .eq(
                "breaker_key",
                breaker_key
            )
            .execute()
        )

    def _run_insert(self, payload: dict) -> dict:
        response = (
            self.client
            .table(self.table_name)
            .insert(payload)
            .execute()
        )
        return response.data[0]

    # ==========================================
    # GET BREAKER
    # ==========================================

    def list_breakers(self) -> list[dict]:
        response = (
            self.client
            .table(self.table_name)
            .select("*")
            .order("breaker_key", desc=False)
            .execute()
        )
        return response.data or []

    def get_breaker(
        self,
        breaker_key: str,
    ):

        response = (
            self.client
            .table(self.table_name)
            .select("*")
            .eq(
                "breaker_key",
                breaker_key
            )
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]

    # ==========================================
    # CREATE BREAKER
    # ==========================================

    def create_breaker(
        self,
        breaker: CircuitBreaker,
    ):

        payload = breaker.model_dump(
            mode="json",
            exclude_none=True
        )

        if self._supports_half_open_success_count is False:
            payload = _strip_optional_columns(payload)

        try:
            return self._run_insert(payload)
        except APIError as error:
            if (
                self._supports_half_open_success_count is not False
                and _is_missing_column_error(
                    error,
                    "half_open_success_count",
                )
            ):
                self._mark_half_open_column_unsupported()
                return self._run_insert(
                    _strip_optional_columns(payload)
                )
            raise

    # ==========================================
    # UPDATE BREAKER
    # ==========================================

    def update_breaker(
        self,
        breaker_key: str,
        data: dict,
    ):

        payload = dict(data)

        if self._supports_half_open_success_count is False:
            payload = _strip_optional_columns(payload)
            self._run_update(breaker_key, payload)
            return

        try:
            self._run_update(breaker_key, payload)
        except APIError as error:
            if not _is_missing_column_error(
                error,
                "half_open_success_count",
            ):
                raise

            self._mark_half_open_column_unsupported()
            self._run_update(
                breaker_key,
                _strip_optional_columns(data),
            )
