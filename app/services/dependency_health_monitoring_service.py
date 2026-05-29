KNOWN_DEPENDENCIES = [
    "database",
    "queue",
    "scheduler",
    "openai",
    "anthropic",
    "gemini",
    "storage",
]


class DependencyHealthMonitoringService:
    def monitor_dependencies(self, breakers: list[dict]) -> list[dict]:
        breaker_index = {
            breaker.get("breaker_key"): breaker
            for breaker in breakers
        }

        results = []
        for dependency in KNOWN_DEPENDENCIES:
            breaker = (
                breaker_index.get(dependency)
                or breaker_index.get(f"ai:{dependency}")
                or breaker_index.get(f"automation:{dependency}")
            )
            results.append(self._build_dependency_status(dependency, breaker))

        return results

    def get_dependency_summary(self, breakers: list[dict]) -> dict:
        statuses = self.monitor_dependencies(breakers)
        unhealthy = [
            item
            for item in statuses
            if item["status"] != "HEALTHY"
        ]
        return {
            "total_dependencies": len(statuses),
            "healthy_count": len(statuses) - len(unhealthy),
            "unhealthy_count": len(unhealthy),
            "dependencies": statuses,
        }

    def _build_dependency_status(
        self,
        dependency: str,
        breaker: dict | None,
    ) -> dict:
        if not breaker:
            return {
                "dependency": dependency,
                "status": "HEALTHY",
                "breaker_state": None,
                "latency_impact": "NONE",
            }

        state = breaker.get("state", "CLOSED")
        if state == "OPEN":
            status = "UNAVAILABLE"
            latency_impact = "HIGH"
        elif state == "HALF_OPEN":
            status = "DEGRADED"
            latency_impact = "MEDIUM"
        elif breaker.get("failure_count", 0) > 0:
            status = "DEGRADED"
            latency_impact = "LOW"
        else:
            status = "HEALTHY"
            latency_impact = "NONE"

        return {
            "dependency": dependency,
            "status": status,
            "breaker_state": state,
            "latency_impact": latency_impact,
            "failure_count": breaker.get("failure_count", 0),
        }
