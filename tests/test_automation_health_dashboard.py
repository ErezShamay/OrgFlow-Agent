from app.services.automation_monitoring_service import (
    AutomationMonitoringService
)


def build_service():

    return AutomationMonitoringService.__new__(
        AutomationMonitoringService
    )


def test_build_run_summary_counts_health_metrics():

    service = (
        build_service()
    )

    summary = service.build_run_summary([
        {
            "status":
                "COMPLETED",
            "processed_count":
                10,
            "error_count":
                0,
        },
        {
            "status":
                "COMPLETED_WITH_ERRORS",
            "processed_count":
                5,
            "error_count":
                1,
        },
        {
            "status":
                "FAILED",
            "processed_count":
                0,
            "error_count":
                1,
        },
        {
            "status":
                "SKIPPED",
            "processed_count":
                0,
            "error_count":
                0,
        },
    ])

    assert summary["total_runs"] == 4
    assert summary["completed_runs"] == 1
    assert summary["completed_with_errors"] == 1
    assert summary["failed_runs"] == 1
    assert summary["skipped_runs"] == 1
    assert summary["processed_count"] == 15
    assert summary["error_count"] == 2
    assert summary["success_rate"] == 50
    assert summary["error_rate"] == 13.3


def test_resolve_dashboard_health_prioritizes_critical():

    service = (
        build_service()
    )

    health = service.resolve_dashboard_health(

        summary={
            "failed_runs":
                1,
            "completed_with_errors":
                0,
        },

        circuit_breaker_summary={
            "open":
                0,
            "half_open":
                0,
        },

        ai_recovery={
            "dead_letter_count":
                0,
            "recovery_queue_count":
                0,
        },
    )

    assert health == "CRITICAL"


def test_resolve_dashboard_health_detects_degraded():

    service = (
        build_service()
    )

    health = service.resolve_dashboard_health(

        summary={
            "failed_runs":
                0,
            "completed_with_errors":
                1,
        },

        circuit_breaker_summary={
            "open":
                0,
            "half_open":
                0,
        },

        ai_recovery={
            "dead_letter_count":
                0,
            "recovery_queue_count":
                0,
        },
    )

    assert health == "DEGRADED"


def test_build_job_health_groups_runs_by_job():

    service = (
        build_service()
    )

    jobs = service.build_job_health([
        {
            "job_name":
                "sla_monitoring",
            "status":
                "COMPLETED",
            "started_at":
                "2026-05-27T10:00:00Z",
            "completed_at":
                "2026-05-27T10:01:00Z",
            "processed_count":
                4,
            "error_count":
                0,
        },
        {
            "job_name":
                "ai_recovery",
            "status":
                "FAILED",
            "started_at":
                "2026-05-27T10:02:00Z",
            "completed_at":
                "2026-05-27T10:03:00Z",
            "processed_count":
                0,
            "error_count":
                1,
        },
    ])

    assert [
        job["job_name"]
        for job
        in jobs
    ] == [
        "ai_recovery",
        "sla_monitoring",
    ]

    assert jobs[0]["health"] == "CRITICAL"
    assert jobs[1]["health"] == "HEALTHY"
