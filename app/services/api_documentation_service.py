from __future__ import annotations

API_DOCS_CONFIG = {
    "spec_format": "openapi_3.1",
    "spec_path": "/openapi.json",
    "ui_path": "/docs",
    "auth_documented": True,
}


class ApiDocumentationService:
    def get_config(self) -> dict:
        return API_DOCS_CONFIG

    def list_documented_groups(self) -> dict:
        groups = [
            {"tag": "projects", "endpoints": 12},
            {"tag": "reports", "endpoints": 15},
            {"tag": "auth", "endpoints": 8},
            {"tag": "portfolio", "endpoints": 10},
            {"tag": "product-readiness", "endpoints": 40},
        ]
        return {"groups": groups, "total": len(groups)}

    def evaluate_completeness(self, *, documented_tags: list[str]) -> dict:
        expected = {g["tag"] for g in self.list_documented_groups()["groups"]}
        documented = set(documented_tags)
        ratio = len(documented & expected) / len(expected) if expected else 0
        return {
            "complete": ratio >= 0.9,
            "coverage_percent": round(ratio * 100, 1),
            "missing_tags": sorted(expected - documented),
        }

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "spec_format": API_DOCS_CONFIG["spec_format"],
            "groups_documented": self.list_documented_groups()["total"] >= 4,
        }
