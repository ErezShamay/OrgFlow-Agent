class AutoRecoveryRulesService:
    def __init__(self):
        self._rules = [
            {
                "id": "timeout-retry",
                "failure_type": "TIMEOUT",
                "min_severity": "LOW",
                "max_retry_count": 2,
                "enabled": True,
                "action": "RETRY",
            },
            {
                "id": "rate-limit-retry",
                "failure_type": "RATE_LIMIT",
                "min_severity": "LOW",
                "max_retry_count": 3,
                "enabled": True,
                "action": "RETRY",
            },
            {
                "id": "permission-skip",
                "failure_type": "PERMISSION",
                "min_severity": "HIGH",
                "max_retry_count": 0,
                "enabled": True,
                "action": "SKIP",
            },
            {
                "id": "data-error-skip",
                "failure_type": "DATA_ERROR",
                "min_severity": "HIGH",
                "max_retry_count": 0,
                "enabled": True,
                "action": "SKIP",
            },
        ]
        self._severity_rank = {
            "LOW": 1,
            "MEDIUM": 2,
            "HIGH": 3,
        }

    def list_rules(self):
        return list(self._rules)

    def evaluate(
        self,
        log: dict,
    ):
        failure_type = log.get("failure_type", "UNKNOWN")
        severity = log.get("severity", "MEDIUM")
        retry_count = log.get("retry_count", 0)

        for rule in self._rules:
            if not rule["enabled"]:
                continue
            if rule["failure_type"] != failure_type:
                continue
            if retry_count > rule["max_retry_count"]:
                continue
            if (
                self._severity_rank.get(severity, 0)
                < self._severity_rank.get(rule["min_severity"], 0)
            ):
                continue
            return {
                "matched": True,
                "rule_id": rule["id"],
                "action": rule["action"],
                "failure_type": failure_type,
            }

        return {
            "matched": False,
            "rule_id": None,
            "action": "MANUAL_REVIEW",
            "failure_type": failure_type,
        }
