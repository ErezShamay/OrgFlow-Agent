from datetime import datetime, timezone


class OutageDetectionService:
    def detect_outages(self, breakers: list[dict]) -> list[dict]:
        outages = []
        now = datetime.now(timezone.utc)

        for breaker in breakers:
            if breaker.get("state") != "OPEN":
                continue

            breaker_key = breaker.get("breaker_key", "unknown")
            last_failure_at = breaker.get("last_failure_at")
            started_at = last_failure_at or breaker.get("created_at")

            outages.append({
                "breaker_key": breaker_key,
                "service": breaker_key.split(":", 1)[0],
                "severity": self._resolve_severity(breaker),
                "failure_count": breaker.get("failure_count", 0),
                "started_at": started_at,
                "detected_at": now.isoformat(),
                "cooldown_until": breaker.get("cooldown_until"),
            })

        return outages

    def get_outage_summary(self, breakers: list[dict]) -> dict:
        outages = self.detect_outages(breakers)
        by_service: dict[str, int] = {}
        for outage in outages:
            service = outage["service"]
            by_service[service] = by_service.get(service, 0) + 1

        return {
            "active_outage_count": len(outages),
            "outages": outages,
            "by_service": by_service,
        }

    def _resolve_severity(self, breaker: dict) -> str:
        failure_count = breaker.get("failure_count", 0)
        if failure_count >= 10:
            return "CRITICAL"
        if failure_count >= 5:
            return "HIGH"
        return "MEDIUM"
