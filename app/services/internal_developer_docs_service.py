from __future__ import annotations

DEV_DOCS_CONFIG = {
    "base_path": "docs/internal",
    "audience": "engineering",
    "includes_runbooks": True,
    "includes_architecture_diagrams": True,
}


class InternalDeveloperDocsService:
    def get_config(self) -> dict:
        return DEV_DOCS_CONFIG

    def list_guides(self) -> dict:
        guides = [
            {"id": "local_setup", "category": "onboarding"},
            {"id": "database_migrations", "category": "data"},
            {"id": "ai_providers", "category": "ai"},
            {"id": "deployment", "category": "devops"},
            {"id": "incident_response", "category": "operations"},
        ]
        return {"guides": guides, "total": len(guides)}

    def evaluate_onboarding_pack(self, *, available_guides: list[str]) -> dict:
        required = {"local_setup", "database_migrations", "deployment"}
        available = set(available_guides)
        return {
            "complete": required.issubset(available),
            "missing": sorted(required - available),
        }

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "guides_available": self.list_guides()["total"] >= 4,
            "runbooks": DEV_DOCS_CONFIG["includes_runbooks"],
        }
