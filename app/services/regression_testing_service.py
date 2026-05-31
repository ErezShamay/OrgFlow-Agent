from __future__ import annotations

REGRESSION_CONFIG = {
    "strategy": "snapshot_and_golden",
    "ci_on_pull_request": True,
    "baseline_branch": "main",
}


class RegressionTestingService:
    def get_config(self) -> dict:
        return REGRESSION_CONFIG

    def list_suites(self) -> dict:
        suites = [
            {"id": "api_responses", "snapshots": 45, "flaky_tolerance": 0},
            {"id": "portfolio_insights", "snapshots": 12, "flaky_tolerance": 0},
            {"id": "ui_components", "snapshots": 8, "flaky_tolerance": 1},
        ]
        return {"suites": suites, "total": len(suites)}

    def compare_baseline(
        self,
        *,
        suite_id: str,
        changed_snapshots: int = 0,
    ) -> dict:
        suites = {s["id"]: s for s in self.list_suites()["suites"]}
        suite = suites.get(suite_id)
        if not suite:
            return {"found": False, "passed": False}
        return {
            "found": True,
            "suite_id": suite_id,
            "changed_snapshots": changed_snapshots,
            "passed": changed_snapshots <= suite["flaky_tolerance"],
        }

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "ci_on_pull_request": REGRESSION_CONFIG["ci_on_pull_request"],
            "suite_count": self.list_suites()["total"] >= 2,
        }
