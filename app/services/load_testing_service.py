from __future__ import annotations

LOAD_TEST_CONFIG = {
    "tool": "k6",
    "default_vus": 50,
    "default_duration": "5m",
    "thresholds": {"p95_ms": 500, "error_rate_percent": 1.0},
}


class LoadTestingService:
    def get_config(self) -> dict:
        return LOAD_TEST_CONFIG

    def list_scenarios(self) -> dict:
        scenarios = [
            {"id": "api_read_heavy", "vus": 100, "rps_target": 500},
            {"id": "report_upload_burst", "vus": 20, "rps_target": 10},
            {"id": "websocket_feed", "vus": 200, "rps_target": 1000},
        ]
        return {"scenarios": scenarios, "total": len(scenarios)}

    def evaluate_results(
        self,
        *,
        p95_ms: float,
        error_rate_percent: float,
    ) -> dict:
        thresholds = LOAD_TEST_CONFIG["thresholds"]
        return {
            "p95_ms": p95_ms,
            "error_rate_percent": error_rate_percent,
            "passed": (
                p95_ms <= thresholds["p95_ms"]
                and error_rate_percent <= thresholds["error_rate_percent"]
            ),
            "thresholds": thresholds,
        }

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "tool": LOAD_TEST_CONFIG["tool"],
            "scenario_count": self.list_scenarios()["total"] >= 2,
        }
