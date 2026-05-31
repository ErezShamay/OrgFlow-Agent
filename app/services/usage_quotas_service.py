from __future__ import annotations

USAGE_QUOTAS_CONFIG = {
    "enforcement": "soft_then_hard",
    "reset_period": "monthly",
    "overage_billing": True,
}


class UsageQuotasService:
    def get_config(self) -> dict:
        return USAGE_QUOTAS_CONFIG

    def list_quotas(self) -> dict:
        quotas = [
            {"metric": "ai_tokens", "starter": 50_000, "growth": 250_000, "enterprise": -1},
            {"metric": "reports", "starter": 100, "growth": 500, "enterprise": -1},
            {"metric": "projects", "starter": 10, "growth": 50, "enterprise": -1},
            {"metric": "storage_gb", "starter": 5, "growth": 50, "enterprise": -1},
        ]
        return {"quotas": quotas, "total": len(quotas)}

    def check_usage(
        self,
        *,
        metric: str,
        plan: str,
        current_usage: int,
    ) -> dict:
        quota_row = next(
            (q for q in self.list_quotas()["quotas"] if q["metric"] == metric),
            None,
        )
        if quota_row is None:
            return {"allowed": False, "error": "unknown_metric"}
        limit = quota_row.get(plan, 0)
        if limit < 0:
            return {"allowed": True, "metric": metric, "unlimited": True}
        return {
            "allowed": current_usage < limit,
            "metric": metric,
            "limit": limit,
            "current_usage": current_usage,
            "remaining": max(limit - current_usage, 0),
        }

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "quotas_defined": self.list_quotas()["total"] >= 3,
            "enforcement": USAGE_QUOTAS_CONFIG["enforcement"],
        }
