from __future__ import annotations

UNIT_TEST_CONFIG = {
    "framework": "pytest",
    "coverage_threshold_percent": 80,
    "test_directory": "tests",
    "parallel_workers": 4,
    "markers": ["unit", "slow", "integration"],
}


class UnitTestsService:
    def get_config(self) -> dict:
        return UNIT_TEST_CONFIG

    def list_suites(self) -> dict:
        suites = [
            {"id": "auth", "path": "tests/test_auth.py", "tests": 12},
            {"id": "projects", "path": "tests/test_projects.py", "tests": 18},
            {"id": "reports", "path": "tests/test_reports.py", "tests": 15},
            {"id": "services", "path": "tests/test_*_backlog.py", "tests": 90},
        ]
        return {"suites": suites, "total": len(suites)}

    def evaluate_coverage(self, *, coverage_percent: float) -> dict:
        threshold = UNIT_TEST_CONFIG["coverage_threshold_percent"]
        return {
            "coverage_percent": coverage_percent,
            "threshold_percent": threshold,
            "met": coverage_percent >= threshold,
        }

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "framework": UNIT_TEST_CONFIG["framework"],
            "coverage_threshold": UNIT_TEST_CONFIG["coverage_threshold_percent"],
            "suites_available": self.list_suites()["total"] >= 3,
        }
