from uuid import uuid4

from datetime import (
    datetime,
    timedelta,
    timezone,
)

from app.schemas.circuit_breaker import (
    CircuitBreaker
)

from app.repositories.circuit_breaker_repository import (
    CircuitBreakerRepository
)

from app.services.circuit_breaker_threshold_service import (
    CircuitBreakerThresholdService,
)


class CircuitBreakerService:

    def __init__(
        self,
        repository: CircuitBreakerRepository | None = None,
        threshold_service: CircuitBreakerThresholdService | None = None,
    ):

        self.repository = repository or CircuitBreakerRepository()

        self.threshold_service = (
            threshold_service or CircuitBreakerThresholdService()
        )

    def list_breakers(self) -> list[dict]:
        return self.repository.list_breakers()

    # ==========================================
    # ALLOW REQUEST
    # ==========================================

    def allow_request(
        self,
        breaker_key: str,
    ):

        breaker = (
            self.repository
            .get_breaker(
                breaker_key
            )
        )

        if not breaker:

            breaker = (
                CircuitBreaker(

                    id=str(uuid4()),

                    breaker_key=
                        breaker_key,

                    state=
                        "CLOSED",
                )
            )

            self.repository.create_breaker(
                breaker
            )

            return True

        state = (
            breaker.get(
                "state"
            )
        )

        if state == "CLOSED":
            return True

        cooldown_until = (
            breaker.get(
                "cooldown_until"
            )
        )

        if not cooldown_until:
            return False

        cooldown_until = (
            datetime.fromisoformat(
                cooldown_until.replace(
                    "Z",
                    "+00:00"
                )
            )
        )

        now = (
            datetime.now(
                timezone.utc
            )
        )

        # ======================================
        # HALF OPEN TRANSITION
        # ======================================

        if now >= cooldown_until:

            self.repository.update_breaker(

                breaker_key,

                {
                    "state":
                        "HALF_OPEN",
                    "half_open_success_count": 0,
                }
            )

            return True

        return False

    # ==========================================
    # RECORD SUCCESS
    # ==========================================

    def record_success(
        self,
        breaker_key: str,
    ):

        breaker = self.repository.get_breaker(breaker_key)
        if not breaker:
            return

        state = breaker.get("state", "CLOSED")
        threshold = self.threshold_service.get_threshold(breaker_key)

        if state == "HALF_OPEN":
            supports_half_open_count = getattr(
                self.repository,
                "supports_half_open_success_count",
                None,
            )
            if callable(supports_half_open_count):
                column_supported = supports_half_open_count()
            else:
                column_supported = True

            if not column_supported:
                self.repository.update_breaker(
                    breaker_key,
                    {
                        "state": "CLOSED",
                        "failure_count": 0,
                        "cooldown_until": None,
                    },
                )
                return

            success_count = breaker.get("half_open_success_count", 0) + 1
            if success_count >= threshold["half_open_success_threshold"]:
                self.repository.update_breaker(
                    breaker_key,
                    {
                        "state": "CLOSED",
                        "failure_count": 0,
                        "half_open_success_count": 0,
                        "cooldown_until": None,
                    },
                )
                return

            self.repository.update_breaker(
                breaker_key,
                {"half_open_success_count": success_count},
            )
            return

        payload = {
            "state": "CLOSED",
            "failure_count": 0,
        }
        supports_half_open_count = getattr(
            self.repository,
            "supports_half_open_success_count",
            None,
        )
        if callable(supports_half_open_count) and supports_half_open_count():
            payload["half_open_success_count"] = 0

        self.repository.update_breaker(
            breaker_key,
            payload,
        )

    # ==========================================
    # RECORD FAILURE
    # ==========================================

    def record_failure(
        self,
        breaker_key: str,
    ):

        breaker = (
            self.repository
            .get_breaker(
                breaker_key
            )
        )

        if not breaker:
            return

        threshold = self.threshold_service.get_threshold(breaker_key)
        failure_threshold = threshold["failure_threshold"]
        cooldown_minutes = threshold["cooldown_minutes"]

        failure_count = (
            breaker.get(
                "failure_count",
                0
            ) + 1
        )

        data = {

            "failure_count":
                failure_count,

            "last_failure_at":
                datetime.now(
                    timezone.utc
                ).isoformat(),
        }

        if breaker.get("state") == "HALF_OPEN":
            data["state"] = "OPEN"
            data["half_open_success_count"] = 0
            data["cooldown_until"] = (
                datetime.now(timezone.utc)
                + timedelta(minutes=cooldown_minutes)
            ).isoformat()
            self.repository.update_breaker(breaker_key, data)
            return

        # ======================================
        # OPEN CIRCUIT
        # ======================================

        if failure_count >= failure_threshold:

            data["state"] = "OPEN"

            data["cooldown_until"] = (

                datetime.now(
                    timezone.utc
                )

                + timedelta(
                    minutes=cooldown_minutes
                )

            ).isoformat()

        self.repository.update_breaker(

            breaker_key,
            data,
        )
