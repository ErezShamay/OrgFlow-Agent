from __future__ import annotations

DEMO_DATA_CONFIG = {
    "generator_id": "orgflow_demo_v1",
    "seed_version": "2026.05",
    "entities": ["organizations", "projects", "reports", "actions", "reviews"],
    "idempotent": True,
}


class DemoDataGeneratorService:
    def get_config(self) -> dict:
        return DEMO_DATA_CONFIG

    def list_presets(self) -> dict:
        presets = [
            {"id": "startup", "projects": 3, "reports_per_project": 4},
            {"id": "enterprise", "projects": 12, "reports_per_project": 8},
            {"id": "portfolio", "projects": 25, "reports_per_project": 6},
        ]
        return {"presets": presets, "total": len(presets)}

    def simulate_generation(self, *, preset_id: str) -> dict:
        presets = {p["id"]: p for p in self.list_presets()["presets"]}
        preset = presets.get(preset_id)
        if preset is None:
            return {"generated": False, "error": "unknown_preset"}
        reports = preset["projects"] * preset["reports_per_project"]
        return {
            "generated": True,
            "preset_id": preset_id,
            "projects_created": preset["projects"],
            "reports_created": reports,
            "seed_version": DEMO_DATA_CONFIG["seed_version"],
        }

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "presets_available": self.list_presets()["total"] >= 3,
            "idempotent": DEMO_DATA_CONFIG["idempotent"],
        }
