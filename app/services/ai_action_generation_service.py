from __future__ import annotations

AI_ACTION_GENERATION_CONFIG = {
    "model_route": "ai_routing_engine",
    "min_confidence": 0.72,
    "max_actions_per_run": 10,
    "source_signals": ["reports", "reviews", "workspace"],
}


class AiActionGenerationService:
    def get_config(self) -> dict:
        return AI_ACTION_GENERATION_CONFIG

    def list_action_types(self) -> dict:
        types = [
            {"id": "follow_up", "label": "Follow-up task"},
            {"id": "escalation", "label": "Escalation"},
            {"id": "review_request", "label": "Review request"},
        ]
        return {"types": types, "total": len(types)}

    def simulate_generation(self, *, project_id: str = "p1", signal_count: int = 3) -> dict:
        capped = min(signal_count, AI_ACTION_GENERATION_CONFIG["max_actions_per_run"])
        return {
            "project_id": project_id,
            "generated": capped > 0,
            "actions_proposed": capped,
            "confidence_avg": 0.81,
        }

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "types_defined": self.list_action_types()["total"] >= 3,
        }
