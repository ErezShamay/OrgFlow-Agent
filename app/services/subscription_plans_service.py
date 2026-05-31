from __future__ import annotations

SUBSCRIPTION_CONFIG = {
    "trial_days": 14,
    "default_plan": "starter",
    "upgrade_paths": ["starter", "growth", "enterprise"],
}


class SubscriptionPlansService:
    def get_config(self) -> dict:
        return SUBSCRIPTION_CONFIG

    def list_plans(self) -> dict:
        plans = [
            {
                "id": "starter",
                "name": "Starter",
                "trial_eligible": True,
                "features": ["projects", "reports", "ai_reviews"],
            },
            {
                "id": "growth",
                "name": "Growth",
                "trial_eligible": True,
                "features": ["projects", "reports", "ai_reviews", "automation", "portfolio"],
            },
            {
                "id": "enterprise",
                "name": "Enterprise",
                "trial_eligible": False,
                "features": ["all", "sso", "dedicated_support"],
            },
        ]
        return {"plans": plans, "total": len(plans)}

    def evaluate_upgrade(self, *, from_plan: str, to_plan: str) -> dict:
        paths = SUBSCRIPTION_CONFIG["upgrade_paths"]
        if from_plan not in paths or to_plan not in paths:
            return {"allowed": False, "reason": "unknown_plan"}
        return {
            "allowed": paths.index(to_plan) > paths.index(from_plan),
            "from_plan": from_plan,
            "to_plan": to_plan,
        }

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "plans_defined": self.list_plans()["total"] >= 3,
            "trial_days": SUBSCRIPTION_CONFIG["trial_days"],
        }
