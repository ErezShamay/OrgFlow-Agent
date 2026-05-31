class ExecutiveKpiService:
    def get_kpis(self, portfolio_summary: dict) -> dict:
        projects = portfolio_summary.get("projects", [])
        total_projects = portfolio_summary.get("total_projects", len(projects))
        critical_projects = portfolio_summary.get("critical_projects", 0)
        total_actions = portfolio_summary.get("total_actions", 0)
        total_escalations = portfolio_summary.get("total_escalations", 0)
        average_health = portfolio_summary.get("average_health_score", 0)

        risk_scores = [
            project["prediction"]["risk_score"]
            for project in projects
        ]
        average_risk = 0
        if risk_scores:
            average_risk = round(sum(risk_scores) / len(risk_scores), 2)

        critical_ratio = 0.0
        if total_projects > 0:
            critical_ratio = round(critical_projects / total_projects, 4)

        return {
            "portfolio_health_index": average_health,
            "risk_exposure_index": average_risk,
            "operational_load_index": total_actions,
            "escalation_pressure": total_escalations,
            "critical_project_ratio": critical_ratio,
            "total_projects": total_projects,
            "critical_projects": critical_projects,
        }
