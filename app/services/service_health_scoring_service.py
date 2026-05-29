class ServiceHealthScoringService:
    def score_breaker(self, breaker: dict) -> int:
        state = breaker.get("state", "CLOSED")
        failure_count = breaker.get("failure_count", 0)

        if state == "OPEN":
            return max(0, 20 - failure_count)
        if state == "HALF_OPEN":
            return 55
        if failure_count > 0:
            return max(40, 100 - (failure_count * 10))
        return 100

    def score_service(self, service_name: str, breakers: list[dict]) -> dict:
        service_breakers = [
            breaker
            for breaker in breakers
            if str(breaker.get("breaker_key", "")).startswith(
                f"{service_name}:"
            )
            or breaker.get("breaker_key") == service_name
        ]
        if not service_breakers:
            return {
                "service": service_name,
                "score": 100,
                "breaker_count": 0,
                "status": "HEALTHY",
            }

        scores = [self.score_breaker(breaker) for breaker in service_breakers]
        average = round(sum(scores) / len(scores))
        status = self._status_from_score(average)

        return {
            "service": service_name,
            "score": average,
            "breaker_count": len(service_breakers),
            "status": status,
        }

    def get_overall_health_score(self, breakers: list[dict]) -> dict:
        if not breakers:
            return {
                "score": 100,
                "status": "HEALTHY",
                "service_scores": [],
            }

        services = sorted({
            breaker.get("breaker_key", "").split(":", 1)[0]
            for breaker in breakers
            if breaker.get("breaker_key")
        })
        service_scores = [
            self.score_service(service, breakers)
            for service in services
        ]
        overall = round(
            sum(item["score"] for item in service_scores) / len(service_scores)
        )
        return {
            "score": overall,
            "status": self._status_from_score(overall),
            "service_scores": service_scores,
        }

    def _status_from_score(self, score: int) -> str:
        if score >= 80:
            return "HEALTHY"
        if score >= 50:
            return "DEGRADED"
        return "CRITICAL"
