from __future__ import annotations

PRODUCT_DEMO_CONFIG = {
    "demo_id": "orgflow_product_demo_v1",
    "target_duration_minutes": 20,
    "modes": ["live", "self_serve", "recorded"],
    "default_mode": "live",
}


class ProductDemoService:
    def get_config(self) -> dict:
        return PRODUCT_DEMO_CONFIG

    def list_scenarios(self) -> dict:
        scenarios = [
            {
                "id": "portfolio_overview",
                "title": "Portfolio overview",
                "duration_minutes": 4,
                "required": True,
            },
            {
                "id": "ai_report_review",
                "title": "AI report review",
                "duration_minutes": 5,
                "required": True,
            },
            {
                "id": "operational_actions",
                "title": "Operational actions",
                "duration_minutes": 4,
                "required": True,
            },
            {
                "id": "automation_preview",
                "title": "Automation preview",
                "duration_minutes": 3,
                "required": False,
            },
            {
                "id": "executive_insights",
                "title": "Executive insights",
                "duration_minutes": 4,
                "required": True,
            },
        ]
        return {"scenarios": scenarios, "total": len(scenarios)}

    def evaluate_readiness(self, *, completed_scenarios: list[str]) -> dict:
        required = {
            s["id"]
            for s in self.list_scenarios()["scenarios"]
            if s["required"]
        }
        done = set(completed_scenarios)
        missing = sorted(required - done)
        return {
            "demo_ready": not missing,
            "completed": len(done),
            "total": self.list_scenarios()["total"],
            "missing_required": missing,
        }

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "demo_id": PRODUCT_DEMO_CONFIG["demo_id"],
            "scenarios_defined": self.list_scenarios()["total"] >= 4,
        }
