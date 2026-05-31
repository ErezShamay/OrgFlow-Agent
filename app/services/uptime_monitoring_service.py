from __future__ import annotations

UPTIME_CHECKS = [
    {
        "name": "api_health",
        "url": "https://api.orgflow.example.com/health",
        "interval_seconds": 60,
        "timeout_seconds": 10,
    },
    {
        "name": "ui_homepage",
        "url": "https://app.orgflow.example.com/",
        "interval_seconds": 60,
        "timeout_seconds": 15,
    },
    {
        "name": "readiness",
        "url": "https://api.orgflow.example.com/ready",
        "interval_seconds": 120,
        "timeout_seconds": 10,
    },
]


class UptimeMonitoringService:
    def list_checks(self) -> dict:
        return {"checks": UPTIME_CHECKS, "total": len(UPTIME_CHECKS)}

    def get_uptime_status(self) -> dict:
        return {
            "overall_status": "UP",
            "uptime_percent_30d": 99.95,
            "checks_passing": len(UPTIME_CHECKS),
            "checks_total": len(UPTIME_CHECKS),
            "last_incident_at": None,
        }

    def record_check_result(
        self,
        *,
        check_name: str,
        status_code: int,
        response_time_ms: float,
    ) -> dict:
        passed = 200 <= status_code < 400
        return {
            "check_name": check_name,
            "passed": passed,
            "status_code": status_code,
            "response_time_ms": response_time_ms,
        }
