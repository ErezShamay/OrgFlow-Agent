from __future__ import annotations

INTEGRATION_CONFIG = {
    "framework": "pytest",
    "database_fixture": "postgresql",
    "isolation": "transaction_rollback",
    "external_mocks": ["ai_providers", "email", "storage"],
}


class IntegrationTestsService:
    def get_config(self) -> dict:
        return INTEGRATION_CONFIG

    def list_scenarios(self) -> dict:
        scenarios = [
            {"id": "project_crud", "components": ["api", "db", "auth"]},
            {"id": "report_upload", "components": ["api", "db", "storage"]},
            {"id": "automation_run", "components": ["api", "db", "worker", "queue"]},
            {"id": "tenant_isolation", "components": ["api", "db", "rls"]},
        ]
        return {"scenarios": scenarios, "total": len(scenarios)}

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "database_fixture": INTEGRATION_CONFIG["database_fixture"],
            "scenario_count": self.list_scenarios()["total"] >= 3,
            "mocks_configured": len(INTEGRATION_CONFIG["external_mocks"]) >= 2,
        }
