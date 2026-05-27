from app.db.supabase_client import (
    supabase
)


class AutomationMonitoringService:

    def __init__(self):

        self.client = (
            supabase
        )

    # ==========================================
    # GET RECENT RUNS
    # ==========================================

    def get_recent_runs(
        self,
        limit: int = 20,
    ):

        response = (
            self.client
            .table("automation_runs")
            .select("*")
            .order(
                "started_at",
                desc=True
            )
            .limit(limit)
            .execute()
        )

        return response.data

    # ==========================================
    # GET AUTOMATION STATS
    # ==========================================

    def get_automation_stats(
        self,
    ):

        runs = (
            self.get_recent_runs(
                100
            )
        )

        total_runs = len(runs)

        completed_runs = len([

            run for run in runs

            if run["status"]
            == "COMPLETED"
        ])

        failed_runs = len([

            run for run in runs

            if run["status"]
            == "COMPLETED_WITH_ERRORS"
        ])

        processed_count = sum([

            run.get(
                "processed_count",
                0
            )

            for run in runs
        ])

        error_count = sum([

            run.get(
                "error_count",
                0
            )

            for run in runs
        ])

        health = (
            "HEALTHY"
            if failed_runs == 0
            else "DEGRADED"
        )

        return {

            "health":
                health,

            "total_runs":
                total_runs,

            "completed_runs":
                completed_runs,

            "failed_runs":
                failed_runs,

            "processed_count":
                processed_count,

            "error_count":
                error_count,
        }