class ExecutiveSummaryService:
    def generate(
        self,
        portfolio_summary: dict,
        executive_kpis: dict,
        trend_analysis: dict,
        risk_analysis: dict,
        predictive_alerts: dict,
    ) -> dict:
        total_projects = portfolio_summary.get("total_projects", 0)
        critical_projects = portfolio_summary.get("critical_projects", 0)
        average_health = portfolio_summary.get("average_health_score", 0)
        dominant_trend = trend_analysis.get("dominant_trend", "STABLE")
        portfolio_risk = risk_analysis.get("portfolio_risk_level", "LOW")
        alert_count = predictive_alerts.get("total_alerts", 0)

        headline = (
            f"תיק של {total_projects} פרויקטים במצב {portfolio_risk} "
            f"עם Health ממוצע {average_health}"
        )

        highlights = [
            f"{critical_projects} פרויקטים במצב קריטי",
            f"מגמה דומיננטית: {dominant_trend}",
            f"{alert_count} התראות חיזוייות פעילות",
        ]

        if executive_kpis.get("escalation_pressure", 0) > 0:
            highlights.append(
                f"{executive_kpis['escalation_pressure']} הסלמות פתוחות בתיק"
            )

        return {
            "headline": headline,
            "highlights": highlights,
            "executive_brief": (
                " ".join(highlights)
            ),
            "recommended_focus": self._recommended_focus(
                portfolio_risk,
                dominant_trend,
            ),
        }

    def _recommended_focus(
        self,
        portfolio_risk: str,
        dominant_trend: str,
    ) -> str:
        if portfolio_risk == "HIGH" or dominant_trend == "DECLINING":
            return "IMMEDIATE_INTERVENTION"
        if portfolio_risk == "MEDIUM":
            return "ENHANCED_MONITORING"
        return "MAINTAIN_STABILITY"
