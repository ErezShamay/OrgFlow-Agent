from __future__ import annotations

AUTOMATION_METRICS = [
    {"name": "automation_jobs_processed_total", "type": "counter", "labels": ["status"]},
    {"name": "automation_job_duration_seconds", "type": "histogram", "labels": ["workflow"]},
    {"name": "automation_queue_depth", "type": "gauge", "labels": ["queue"]},
    {"name": "automation_retries_total", "type": "counter", "labels": ["workflow"]},
    {"name": "automation_dead_letter_total", "type": "counter", "labels": ["workflow"]},
]


class AutomationMetricsService:
    def get_config(self) -> dict:
        return {
            "enabled": True,
            "track_queue_depth": True,
            "track_retries": True,
            "track_dead_letters": True,
        }

    def get_metrics_catalog(self) -> dict:
        return {"metrics": AUTOMATION_METRICS, "total": len(AUTOMATION_METRICS)}

    def get_snapshot(
        self,
        *,
        jobs_processed: int = 0,
        queue_depth: int = 0,
        success_rate: float = 100.0,
    ) -> dict:
        return {
            "jobs_processed_total": jobs_processed,
            "queue_depth": queue_depth,
            "success_rate_percent": success_rate,
        }

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "metrics_defined": len(AUTOMATION_METRICS) >= 5,
            "queue_tracking": True,
        }
