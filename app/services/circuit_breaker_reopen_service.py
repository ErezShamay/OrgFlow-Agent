from datetime import datetime, timezone

from app.services.circuit_breaker_service import CircuitBreakerService
from app.services.circuit_breaker_threshold_service import (
    CircuitBreakerThresholdService,
)


class CircuitBreakerReopenService:
    def __init__(
        self,
        circuit_breaker_service: CircuitBreakerService | None = None,
        threshold_service: CircuitBreakerThresholdService | None = None,
    ):
        self.circuit_breaker_service = (
            circuit_breaker_service or CircuitBreakerService()
        )
        self.threshold_service = (
            threshold_service or CircuitBreakerThresholdService()
        )

    def evaluate_automatic_reopen(self, breaker: dict) -> dict:
        breaker_key = breaker.get("breaker_key", "")
        state = breaker.get("state", "CLOSED")
        cooldown_until = breaker.get("cooldown_until")
        now = datetime.now(timezone.utc)

        if state != "OPEN" or not cooldown_until:
            return {
                "breaker_key": breaker_key,
                "should_reopen": False,
                "reason": "NOT_OPEN",
            }

        cooldown_dt = datetime.fromisoformat(
            cooldown_until.replace("Z", "+00:00")
        )
        if now < cooldown_dt:
            return {
                "breaker_key": breaker_key,
                "should_reopen": False,
                "reason": "COOLDOWN_ACTIVE",
                "cooldown_until": cooldown_until,
            }

        return {
            "breaker_key": breaker_key,
            "should_reopen": True,
            "reason": "COOLDOWN_EXPIRED",
            "next_state": "HALF_OPEN",
        }

    def manual_reopen(
        self,
        breaker_key: str,
        initiated_by: str = "operator",
        force_closed: bool = False,
    ):
        breaker = self.circuit_breaker_service.repository.get_breaker(
            breaker_key
        )
        if not breaker:
            raise LookupError(f"Circuit breaker '{breaker_key}' not found")

        next_state = "CLOSED" if force_closed else "HALF_OPEN"
        update = {
            "state": next_state,
            "failure_count": 0,
            "half_open_success_count": 0,
            "cooldown_until": None,
            "last_reopen_at": datetime.now(timezone.utc).isoformat(),
            "last_reopen_by": initiated_by,
        }
        self.circuit_breaker_service.repository.update_breaker(
            breaker_key,
            update,
        )
        return {
            "breaker_key": breaker_key,
            "state": next_state,
            "initiated_by": initiated_by,
            "force_closed": force_closed,
        }

    def process_automatic_reopens(self, breakers: list[dict]) -> list[dict]:
        reopened = []
        for breaker in breakers:
            decision = self.evaluate_automatic_reopen(breaker)
            if not decision["should_reopen"]:
                continue
            result = self.manual_reopen(
                breaker["breaker_key"],
                initiated_by="system",
            )
            reopened.append(result)
        return reopened
