from __future__ import annotations

AI_COPILOTS_CONFIG = {
    "copilot_suite": "orgflow_copilots_v1",
    "domains": ["projects", "reports", "actions", "automation"],
    "shared_memory": True,
}


class AiCopilotsService:
    def get_config(self) -> dict:
        return AI_COPILOTS_CONFIG

    def list_copilots(self) -> dict:
        copilots = [
            {"id": "project_copilot", "domain": "projects"},
            {"id": "report_copilot", "domain": "reports"},
            {"id": "action_copilot", "domain": "actions"},
        ]
        return {"copilots": copilots, "total": len(copilots)}

    def invoke(self, *, copilot_id: str = "project_copilot", prompt_length: int = 50) -> dict:
        return {
            "copilot_id": copilot_id,
            "invoked": prompt_length > 0,
            "used_shared_memory": AI_COPILOTS_CONFIG["shared_memory"],
        }

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "copilots_defined": self.list_copilots()["total"] >= 3,
        }
