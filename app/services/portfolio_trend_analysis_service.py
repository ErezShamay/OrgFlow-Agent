class PortfolioTrendAnalysisService:
    def analyze(self, portfolio_summary: dict) -> dict:
        projects = portfolio_summary.get("projects", [])
        trends = []
        declining = 0
        improving = 0
        stable = 0

        for project in projects:
            health_score = project["health"]["score"]
            risk_score = project["prediction"]["risk_score"]

            if health_score < 50 or risk_score >= 70:
                direction = "DECLINING"
                declining += 1
            elif health_score >= 80 and risk_score < 40:
                direction = "IMPROVING"
                improving += 1
            else:
                direction = "STABLE"
                stable += 1

            trends.append({
                "project_id": project["project_id"],
                "project_name": project["project_name"],
                "direction": direction,
                "health_score": health_score,
                "risk_score": risk_score,
            })

        total = len(projects)
        if declining >= improving and declining >= stable:
            dominant_trend = "DECLINING"
        elif improving >= stable:
            dominant_trend = "IMPROVING"
        else:
            dominant_trend = "STABLE"

        return {
            "trends": trends,
            "summary": {
                "declining": declining,
                "improving": improving,
                "stable": stable,
                "total_projects": total,
            },
            "dominant_trend": dominant_trend,
        }
