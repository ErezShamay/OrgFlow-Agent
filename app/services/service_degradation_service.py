class ServiceDegradationService:
    def get_degradation_mode(self, breakers: list[dict]) -> dict:
        open_breakers = [
            breaker
            for breaker in breakers
            if breaker.get("state") == "OPEN"
        ]
        half_open_breakers = [
            breaker
            for breaker in breakers
            if breaker.get("state") == "HALF_OPEN"
        ]

        if len(open_breakers) >= 3:
            mode = "CRITICAL"
        elif open_breakers:
            mode = "DEGRADED"
        elif half_open_breakers:
            mode = "RECOVERING"
        else:
            mode = "HEALTHY"

        affected_services = sorted({
            self._resolve_service_name(breaker.get("breaker_key", ""))
            for breaker in open_breakers + half_open_breakers
        })

        return {
            "mode": mode,
            "open_breaker_count": len(open_breakers),
            "half_open_breaker_count": len(half_open_breakers),
            "affected_services": affected_services,
            "features_disabled": self._disabled_features(mode),
        }

    def _resolve_service_name(self, breaker_key: str) -> str:
        if ":" in breaker_key:
            return breaker_key.split(":", 1)[0]
        return breaker_key

    def _disabled_features(self, mode: str) -> list[str]:
        if mode == "CRITICAL":
            return [
                "ai_automation",
                "bulk_replay",
                "non_critical_jobs",
            ]
        if mode == "DEGRADED":
            return ["bulk_replay", "non_critical_jobs"]
        return []
