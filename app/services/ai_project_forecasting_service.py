from __future__ import annotations

AI_PROJECT_FORECASTING_CONFIG = {
    "horizon_weeks": 12,
    "model_version": "project_forecast_v2",
    "signals": ["velocity", "escalations", "health_score"],
}


class AiProjectForecastingService:
    def get_config(self) -> dict:
        return AI_PROJECT_FORECASTING_CONFIG

    def forecast_project(self, *, project_id: str = "p1", health_score: int = 55) -> dict:
        risk = "HIGH" if health_score < 50 else "MEDIUM" if health_score < 75 else "LOW"
        return {
            "project_id": project_id,
            "horizon_weeks": AI_PROJECT_FORECASTING_CONFIG["horizon_weeks"],
            "completion_probability": max(10, min(95, health_score)),
            "risk_band": risk,
        }

    def list_forecast_metrics(self) -> dict:
        metrics = ["completion_date", "budget_variance", "escalation_trend"]
        return {"metrics": metrics, "total": len(metrics)}

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "metrics_defined": self.list_forecast_metrics()["total"] >= 3,
        }
