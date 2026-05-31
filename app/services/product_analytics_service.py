from __future__ import annotations

PRODUCT_ANALYTICS_CONFIG = {
    "provider": "posthog",
    "events_enabled": True,
    "pii_redaction": True,
    "retention_days": 365,
}


class ProductAnalyticsService:
    def get_config(self) -> dict:
        return PRODUCT_ANALYTICS_CONFIG

    def list_events(self) -> dict:
        events = [
            {"id": "project_created", "category": "activation"},
            {"id": "report_uploaded", "category": "engagement"},
            {"id": "ai_review_completed", "category": "ai"},
            {"id": "action_completed", "category": "workflow"},
            {"id": "subscription_upgraded", "category": "revenue"},
        ]
        return {"events": events, "total": len(events)}

    def evaluate_tracking(self, *, events_implemented: list[str]) -> dict:
        defined = {e["id"] for e in self.list_events()["events"]}
        implemented = set(events_implemented)
        coverage = len(implemented & defined) / len(defined) if defined else 0
        return {
            "coverage_percent": round(coverage * 100, 1),
            "ready": coverage >= 0.8,
            "missing": sorted(defined - implemented),
        }

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "provider": PRODUCT_ANALYTICS_CONFIG["provider"],
            "events_defined": self.list_events()["total"] >= 4,
        }
