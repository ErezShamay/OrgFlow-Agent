class PortfolioForecastingService:
    def forecast(
        self,
        portfolio_summary: dict,
        horizon_days: int = 30,
    ) -> dict:
        projects = portfolio_summary.get("projects", [])
        current_health = portfolio_summary.get("average_health_score", 0)
        current_actions = portfolio_summary.get("total_actions", 0)
        current_escalations = portfolio_summary.get("total_escalations", 0)

        risk_pressure = sum(
            project["prediction"]["risk_score"]
            for project in projects
        )
        project_count = max(len(projects), 1)
        average_risk = risk_pressure / project_count

        health_delta = int((average_risk / 100) * (horizon_days / 30) * -12)
        action_delta = int((current_actions / project_count) * (horizon_days / 30))
        escalation_delta = int(
            (current_escalations / project_count)
            * (horizon_days / 30)
            * (1 + average_risk / 100)
        )

        projected_health = max(0, min(100, current_health + health_delta))
        projected_actions = current_actions + action_delta
        projected_escalations = current_escalations + escalation_delta

        if projected_health >= 80:
            outlook = "STABLE"
        elif projected_health >= 50:
            outlook = "WATCH"
        else:
            outlook = "AT_RISK"

        return {
            "horizon_days": horizon_days,
            "current": {
                "average_health_score": current_health,
                "total_actions": current_actions,
                "total_escalations": current_escalations,
            },
            "projected": {
                "average_health_score": projected_health,
                "total_actions": projected_actions,
                "total_escalations": projected_escalations,
            },
            "outlook": outlook,
            "confidence": self._confidence(project_count),
        }

    def _confidence(self, project_count: int) -> float:
        if project_count >= 10:
            return 0.85
        if project_count >= 5:
            return 0.7
        if project_count >= 2:
            return 0.55
        return 0.4
