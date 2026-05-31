from __future__ import annotations

DEMO_ENV_CONFIG = {
    "environment": "demo",
    "url": "https://demo.orgflow.example.com",
    "reset_schedule": "daily",
    "auth_mode": "shared_demo_credentials",
}


class DemoEnvironmentService:
    def get_config(self) -> dict:
        return DEMO_ENV_CONFIG

    def list_features(self) -> dict:
        features = [
            {"id": "sample_portfolio", "enabled": True},
            {"id": "ai_reviews", "enabled": True},
            {"id": "automation_preview", "enabled": True},
            {"id": "write_disabled", "enabled": True},
        ]
        return {"features": features, "total": len(features)}

    def evaluate_health(
        self,
        *,
        api_up: bool,
        ui_up: bool,
        data_seeded: bool,
    ) -> dict:
        healthy = api_up and ui_up and data_seeded
        return {
            "healthy": healthy,
            "api_up": api_up,
            "ui_up": ui_up,
            "data_seeded": data_seeded,
            "environment": DEMO_ENV_CONFIG["environment"],
        }

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "url": DEMO_ENV_CONFIG["url"],
            "features_configured": self.list_features()["total"] >= 3,
        }
