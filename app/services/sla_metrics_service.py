from __future__ import annotations

SLA_TARGETS = {
    "api_availability": {"target_percent": 99.9, "window_hours": 24},
    "ai_review_sla": {"target_hours": 4, "window_hours": 24},
    "action_resolution_sla": {"target_hours": 48, "window_hours": 168},
    "automation_completion_sla": {"target_minutes": 30, "window_hours": 24},
}


class SlaMetricsService:
    def get_targets(self) -> dict:
        return {"targets": SLA_TARGETS, "total": len(SLA_TARGETS)}

    def evaluate_sla(
        self,
        *,
        metric: str,
        actual_value: float,
    ) -> dict:
        target = SLA_TARGETS.get(metric)
        if not target:
            return {"found": False, "metric": metric}

        if "target_percent" in target:
            met = actual_value >= target["target_percent"]
            threshold = target["target_percent"]
        elif "target_hours" in target:
            met = actual_value <= target["target_hours"]
            threshold = target["target_hours"]
        else:
            met = actual_value <= target["target_minutes"]
            threshold = target["target_minutes"]

        return {
            "found": True,
            "metric": metric,
            "actual_value": actual_value,
            "threshold": threshold,
            "met": met,
        }

    def get_compliance_summary(
        self,
        *,
        api_availability: float = 99.95,
        ai_review_hours: float = 3.5,
        action_resolution_hours: float = 36.0,
        automation_completion_minutes: float = 12.0,
    ) -> dict:
        checks = [
            self.evaluate_sla(metric="api_availability", actual_value=api_availability),
            self.evaluate_sla(metric="ai_review_sla", actual_value=ai_review_hours),
            self.evaluate_sla(
                metric="action_resolution_sla",
                actual_value=action_resolution_hours,
            ),
            self.evaluate_sla(
                metric="automation_completion_sla",
                actual_value=automation_completion_minutes,
            ),
        ]
        met_count = sum(1 for c in checks if c.get("met"))
        return {
            "checks": checks,
            "met_count": met_count,
            "total": len(checks),
            "compliant": met_count == len(checks),
        }

    def validate_setup(self) -> dict:
        return {
            "valid": len(SLA_TARGETS) >= 4,
            "target_count": len(SLA_TARGETS),
        }
