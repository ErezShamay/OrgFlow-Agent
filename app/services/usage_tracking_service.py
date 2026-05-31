from __future__ import annotations

USAGE_TRACKING_CONFIG = {
    "aggregation_period": "daily",
    "retention_days": 90,
    "dimensions": ["organization_id", "metric", "plan"],
    "export_formats": ["json", "csv"],
}


class UsageTrackingService:
    def get_config(self) -> dict:
        return USAGE_TRACKING_CONFIG

    def list_metrics(self) -> dict:
        metrics = [
            {"id": "ai_tokens", "unit": "tokens", "billable": True},
            {"id": "reports", "unit": "count", "billable": True},
            {"id": "api_requests", "unit": "count", "billable": False},
            {"id": "storage_gb", "unit": "gb", "billable": True},
            {"id": "active_users", "unit": "count", "billable": False},
        ]
        return {"metrics": metrics, "total": len(metrics)}

    def track_usage(
        self,
        *,
        organization_id: str,
        metric: str,
        amount: int,
    ) -> dict:
        metric_ids = {m["id"] for m in self.list_metrics()["metrics"]}
        if metric not in metric_ids:
            return {"recorded": False, "error": "unknown_metric"}
        if amount < 0:
            return {"recorded": False, "error": "invalid_amount"}
        return {
            "recorded": True,
            "organization_id": organization_id,
            "metric": metric,
            "amount": amount,
            "aggregation_period": USAGE_TRACKING_CONFIG["aggregation_period"],
        }

    def summarize_usage(
        self,
        *,
        organization_id: str,
        usage: dict[str, int] | None = None,
    ) -> dict:
        current = usage or {}
        metrics = self.list_metrics()["metrics"]
        breakdown = []
        total_billable = 0

        for metric in metrics:
            value = current.get(metric["id"], 0)
            if metric["billable"]:
                total_billable += value
            breakdown.append({
                "metric": metric["id"],
                "value": value,
                "unit": metric["unit"],
                "billable": metric["billable"],
            })

        return {
            "organization_id": organization_id,
            "metrics": breakdown,
            "total_billable_events": total_billable,
            "tracked_metrics": len(breakdown),
        }

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "metrics_defined": self.list_metrics()["total"] >= 4,
            "retention_days": USAGE_TRACKING_CONFIG["retention_days"],
        }
