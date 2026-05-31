from __future__ import annotations

ALERT_RULES = [
    {
        "id": "HIGH_ERROR_RATE",
        "metric": "http_request_errors_total",
        "condition": "rate > 5%",
        "severity": "critical",
        "channel": "pagerduty",
    },
    {
        "id": "HIGH_LATENCY",
        "metric": "http_request_duration_seconds",
        "condition": "p95 > 2s",
        "severity": "warning",
        "channel": "slack",
    },
    {
        "id": "AI_PROVIDER_DOWN",
        "metric": "ai_request_errors_total",
        "condition": "rate > 10/min",
        "severity": "critical",
        "channel": "pagerduty",
    },
    {
        "id": "AUTOMATION_QUEUE_BACKLOG",
        "metric": "automation_queue_depth",
        "condition": "value > 100",
        "severity": "warning",
        "channel": "email",
    },
    {
        "id": "SLA_BREACH",
        "metric": "sla_compliance_percent",
        "condition": "value < 99",
        "severity": "critical",
        "channel": "pagerduty",
    },
]


class ObservabilityAlertingService:
    def get_config(self) -> dict:
        return {
            "enabled": True,
            "channels": ["email", "slack", "pagerduty"],
            "evaluation_interval_seconds": 60,
            "rule_count": len(ALERT_RULES),
        }

    def list_rules(self) -> dict:
        return {"rules": ALERT_RULES, "total": len(ALERT_RULES)}

    def evaluate_rule(
        self,
        *,
        rule_id: str,
        current_value: float,
    ) -> dict:
        rule = next((r for r in ALERT_RULES if r["id"] == rule_id), None)
        if not rule:
            return {"found": False, "rule_id": rule_id}

        thresholds = {
            "HIGH_ERROR_RATE": 5.0,
            "HIGH_LATENCY": 2.0,
            "AI_PROVIDER_DOWN": 10.0,
            "AUTOMATION_QUEUE_BACKLOG": 100.0,
            "SLA_BREACH": 99.0,
        }
        threshold = thresholds[rule_id]
        if rule_id == "SLA_BREACH":
            firing = current_value < threshold
        else:
            firing = current_value > threshold

        return {
            "found": True,
            "rule_id": rule_id,
            "firing": firing,
            "current_value": current_value,
            "threshold": threshold,
            "severity": rule["severity"],
            "channel": rule["channel"],
        }

    def validate_setup(self) -> dict:
        return {
            "valid": len(ALERT_RULES) >= 5,
            "channels_configured": True,
        }
