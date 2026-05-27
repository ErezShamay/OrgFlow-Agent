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


class CircuitBreakerService:

    def __init__(self):

        self.repository = (
            CircuitBreakerRepository()
        )

        self.failure_threshold = 5

        self.cooldown_minutes = 10

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
                        "HALF_OPEN"
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

        self.repository.update_breaker(

            breaker_key,

            {
                "state":
                    "CLOSED",

                "failure_count":
                    0,
            }
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

        # ======================================
        # OPEN CIRCUIT
        # ======================================

        if failure_count >= self.failure_threshold:

            data["state"] = "OPEN"

            data["cooldown_until"] = (

                datetime.now(
                    timezone.utc
                )

                + timedelta(
                    minutes=self.cooldown_minutes
                )

            ).isoformat()

            print(
                "[CIRCUIT_BREAKER] "
                f"Opened breaker: "
                f"{breaker_key}"
            )

        self.repository.update_breaker(

            breaker_key,
            data,
        )