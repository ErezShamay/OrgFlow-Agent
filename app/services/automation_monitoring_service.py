from app.db.supabase_client import (
    supabase
)

from app.repositories.ai_execution_log_repository import (
    AIExecutionLogRepository
)


class AutomationMonitoringService:

    def __init__(self):

        self.client = (
            supabase
        )

        self.ai_execution_log_repository = (
            AIExecutionLogRepository()
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

    # ==========================================
    # GET CIRCUIT BREAKERS
    # ==========================================

    def get_circuit_breakers(
        self,
    ):

        response = (
            self.client
            .table("circuit_breakers")
            .select("*")
            .order(
                "breaker_key",
                desc=False
            )
            .execute()
        )

        return response.data

    # ==========================================
    # GET AI RECOVERY MONITORING
    # ==========================================

    def get_ai_recovery_monitoring(
        self,
    ):

        recent_executions = (
            self.ai_execution_log_repository
            .get_recent_executions()
        )

        recovery_queue = (
            self.ai_execution_log_repository
            .get_failed_executions()
        )

        dead_letters = (
            self.ai_execution_log_repository
            .get_dead_letters()
        )

        return {

            "recent_executions":
                recent_executions,

            "recovery_queue":
                recovery_queue,

            "dead_letters":
                dead_letters,

            "recent_count":
                len(recent_executions),

            "recovery_queue_count":
                len(recovery_queue),

            "dead_letter_count":
                len(dead_letters),
        }
