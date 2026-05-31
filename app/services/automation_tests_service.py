from __future__ import annotations

AUTOMATION_TEST_CONFIG = {
    "framework": "pytest",
    "worker_simulation": True,
    "queue_fixture": "in_memory",
}


class AutomationTestsService:
    def get_config(self) -> dict:
        return AUTOMATION_TEST_CONFIG

    def list_workflow_tests(self) -> dict:
        tests = [
            {"id": "cron_trigger", "workflow": "scheduled_digest"},
            {"id": "retry_policy", "workflow": "failed_job_retry"},
            {"id": "distributed_lock", "workflow": "concurrent_scheduler"},
            {"id": "pause_resume", "workflow": "automation_control"},
        ]
        return {"tests": tests, "total": len(tests)}

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "worker_simulation": AUTOMATION_TEST_CONFIG["worker_simulation"],
            "workflow_tests": self.list_workflow_tests()["total"] >= 3,
        }
