class CircuitBreakerAnalyticsService:
    def get_analytics(self, breakers: list[dict]) -> dict:
        by_state: dict[str, int] = {}
        by_service: dict[str, int] = {}
        total_failures = 0
        reopen_candidates = 0

        for breaker in breakers:
            state = breaker.get("state", "CLOSED")
            by_state[state] = by_state.get(state, 0) + 1
            service = breaker.get("breaker_key", "unknown").split(":", 1)[0]
            by_service[service] = by_service.get(service, 0) + 1
            total_failures += breaker.get("failure_count", 0)
            if state == "OPEN" and breaker.get("cooldown_until"):
                reopen_candidates += 1

        return {
            "breaker_count": len(breakers),
            "total_recorded_failures": total_failures,
            "by_state": by_state,
            "by_service": by_service,
            "open_rate": self._rate(by_state.get("OPEN", 0), len(breakers)),
            "half_open_rate": self._rate(
                by_state.get("HALF_OPEN", 0),
                len(breakers),
            ),
            "reopen_candidates": reopen_candidates,
        }

    def get_metrics(self, breakers: list[dict]) -> dict:
        analytics = self.get_analytics(breakers)
        return {
            "total_breakers": analytics["breaker_count"],
            "open_count": analytics["by_state"].get("OPEN", 0),
            "half_open_count": analytics["by_state"].get("HALF_OPEN", 0),
            "closed_count": analytics["by_state"].get("CLOSED", 0),
            "total_failures": analytics["total_recorded_failures"],
            "by_service": analytics["by_service"],
        }

    def _rate(self, count: int, total: int) -> float:
        if total == 0:
            return 0.0
        return round(count / total, 4)
