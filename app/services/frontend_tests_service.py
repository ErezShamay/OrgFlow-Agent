from __future__ import annotations

FRONTEND_TEST_CONFIG = {
    "framework": "vitest",
    "runner": "jsdom",
    "ui_package": "orgflow-ui",
    "coverage_threshold_percent": 75,
}


class FrontendTestsService:
    def get_config(self) -> dict:
        return FRONTEND_TEST_CONFIG

    def list_suites(self) -> dict:
        suites = [
            {"id": "lib", "path": "orgflow-ui/tests/lib", "tests": 6},
            {"id": "components", "path": "orgflow-ui/tests/components", "tests": 0},
            {"id": "hooks", "path": "orgflow-ui/tests/hooks", "tests": 0},
        ]
        return {"suites": suites, "total": len(suites)}

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "framework": FRONTEND_TEST_CONFIG["framework"],
            "ui_package": FRONTEND_TEST_CONFIG["ui_package"],
            "lib_tests_present": self.list_suites()["suites"][0]["tests"] >= 1,
        }
