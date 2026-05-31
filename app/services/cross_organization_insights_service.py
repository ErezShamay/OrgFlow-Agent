class CrossOrganizationInsightsService:
    def get_insights(self, organizations: list[dict]) -> dict:
        organization_summaries = []
        total_projects = 0
        total_critical = 0
        health_scores = []

        for organization in organizations:
            projects = organization.get("projects", [])
            critical = 0
            org_health_total = 0

            for project in projects:
                health_score = project.get("health_score", 80)
                org_health_total += health_score
                if health_score < 50:
                    critical += 1

            project_count = len(projects)
            average_health = 0
            if project_count > 0:
                average_health = int(org_health_total / project_count)

            total_projects += project_count
            total_critical += critical
            health_scores.append(average_health)

            organization_summaries.append({
                "organization_id": organization.get("id"),
                "organization_name": organization.get("name"),
                "project_count": project_count,
                "critical_projects": critical,
                "average_health_score": average_health,
            })

        portfolio_average_health = 0
        if health_scores:
            portfolio_average_health = int(
                sum(health_scores) / len(health_scores)
            )

        leaders = sorted(
            organization_summaries,
            key=lambda item: item["average_health_score"],
            reverse=True,
        )

        return {
            "organization_count": len(organizations),
            "total_projects": total_projects,
            "total_critical_projects": total_critical,
            "portfolio_average_health": portfolio_average_health,
            "organizations": organization_summaries,
            "top_performers": leaders[:3],
            "needs_attention": [
                org
                for org in organization_summaries
                if org["critical_projects"] > 0
            ],
        }
