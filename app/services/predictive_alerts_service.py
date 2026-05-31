from app.services.alert_engine_service import AlertEngineService
from app.services.portfolio_forecasting_service import (
    PortfolioForecastingService,
)


class PredictiveAlertsService:
    def __init__(
        self,
        alert_engine_service: AlertEngineService | None = None,
        forecasting_service: PortfolioForecastingService | None = None,
    ):
        self.alert_engine_service = (
            alert_engine_service or AlertEngineService()
        )
        self.forecasting_service = (
            forecasting_service or PortfolioForecastingService()
        )

    def generate(self, portfolio_summary: dict) -> dict:
        base_alerts = self.alert_engine_service.generate_alerts(
            portfolio_summary=portfolio_summary,
        )
        forecast = self.forecasting_service.forecast(portfolio_summary)
        predictive_alerts = list(base_alerts.get("alerts", []))

        if forecast["outlook"] == "AT_RISK":
            predictive_alerts.append({
                "severity": "HIGH",
                "project_id": None,
                "project_name": "Portfolio",
                "title": "תחזית סיכון לתיק",
                "message": (
                    "התחזית מצביעה על הידרדרות צפויה "
                    f"ב-{forecast['horizon_days']} הימים הקרובים"
                ),
                "source": "FORECAST",
            })

        for project in portfolio_summary.get("projects", []):
            if project["prediction"]["prediction"] == "HIGH_RISK":
                predictive_alerts.append({
                    "severity": "CRITICAL",
                    "project_id": project["project_id"],
                    "project_name": project["project_name"],
                    "title": "התראה חיזויית",
                    "message": project["prediction"]["message"],
                    "source": "PREDICTIVE_RISK",
                })

        deduped = self._dedupe(predictive_alerts)

        return {
            "alerts": deduped,
            "total_alerts": len(deduped),
            "forecast_outlook": forecast["outlook"],
        }

    def _dedupe(self, alerts: list[dict]) -> list[dict]:
        seen = set()
        unique = []
        for alert in alerts:
            key = (
                alert.get("project_id"),
                alert.get("title"),
                alert.get("severity"),
            )
            if key in seen:
                continue
            seen.add(key)
            unique.append(alert)
        return unique
