class PortfolioAnalyticsService:
    def get_analytics(self, portfolio_summary: dict) -> dict:
        projects = portfolio_summary.get("projects", [])
        by_health_status: dict[str, int] = {}
        by_risk_level: dict[str, int] = {}
        total_risk_score = 0

        for project in projects:
            health_status = project["health"]["status"]
            by_health_status[health_status] = (
                by_health_status.get(health_status, 0) + 1
            )

            risk_level = project["prediction"]["prediction"]
            by_risk_level[risk_level] = (
                by_risk_level.get(risk_level, 0) + 1
            )
            total_risk_score += project["prediction"]["risk_score"]

        return {
            "project_count": len(projects),
            "by_health_status": by_health_status,
            "by_risk_level": by_risk_level,
            "average_risk_score": (
                round(total_risk_score / len(projects), 2)
                if projects
                else 0
            ),
            "critical_projects": portfolio_summary.get("critical_projects", 0),
            "total_actions": portfolio_summary.get("total_actions", 0),
            "total_escalations": portfolio_summary.get("total_escalations", 0),
        }

    def get_metrics(self, portfolio_summary: dict) -> dict:
        analytics = self.get_analytics(portfolio_summary)
        total_projects = max(analytics["project_count"], 1)

        return {
            "total_projects": analytics["project_count"],
            "critical_projects": analytics["critical_projects"],
            "critical_rate": round(
                analytics["critical_projects"] / total_projects,
                4,
            ),
            "average_health_score": portfolio_summary.get(
                "average_health_score",
                0,
            ),
            "total_actions": analytics["total_actions"],
            "total_escalations": analytics["total_escalations"],
            "high_risk_projects": analytics["by_risk_level"].get("HIGH_RISK", 0),
        }
