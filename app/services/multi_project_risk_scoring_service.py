class MultiProjectRiskScoringService:
    def score_portfolio(self, portfolio_summary: dict) -> dict:
        projects = portfolio_summary.get("projects", [])
        project_scores = []
        total_score = 0

        for project in projects:
            risk_score = project["prediction"]["risk_score"]
            total_score += risk_score
            project_scores.append({
                "project_id": project["project_id"],
                "project_name": project["project_name"],
                "risk_score": risk_score,
                "risk_level": project["prediction"]["prediction"],
                "health_score": project["health"]["score"],
            })

        project_scores.sort(
            key=lambda item: item["risk_score"],
            reverse=True,
        )

        average_score = 0
        if projects:
            average_score = round(total_score / len(projects), 2)

        if average_score >= 70:
            portfolio_risk_level = "HIGH"
        elif average_score >= 40:
            portfolio_risk_level = "MEDIUM"
        else:
            portfolio_risk_level = "LOW"

        return {
            "portfolio_risk_score": average_score,
            "portfolio_risk_level": portfolio_risk_level,
            "project_scores": project_scores,
            "top_risk_projects": project_scores[:5],
        }
