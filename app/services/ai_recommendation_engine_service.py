from __future__ import annotations

AI_RECOMMENDATION_ENGINE_CONFIG = {
    "engine_id": "orgflow_recommendations_v1",
    "ranking_model": "hybrid_collaborative",
    "max_recommendations": 5,
    "contexts": ["project", "portfolio", "workspace"],
}


class AiRecommendationEngineService:
    def get_config(self) -> dict:
        return AI_RECOMMENDATION_ENGINE_CONFIG

    def generate(self, *, context: str = "project", item_count: int = 3) -> dict:
        count = min(item_count, AI_RECOMMENDATION_ENGINE_CONFIG["max_recommendations"])
        return {
            "context": context,
            "recommendations": count,
            "generated": count > 0,
        }

    def list_recommendation_types(self) -> dict:
        types = ["next_action", "risk_mitigation", "resource_allocation"]
        return {"types": types, "total": len(types)}

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "types_defined": self.list_recommendation_types()["total"] >= 3,
        }
