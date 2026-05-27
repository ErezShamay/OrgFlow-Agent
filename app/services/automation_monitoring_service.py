from app.db.supabase_client import (
    supabase
)

from app.repositories.ai_execution_log_repository import (
    AIExecutionLogRepository
)

from datetime import (
    datetime,
    timezone,
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
    # GET AUTOMATION HEALTH DASHBOARD
    # ==========================================

    def get_automation_health_dashboard(
        self,
    ):

        runs = (
            self.get_recent_runs(
                100
            )
        )

        circuit_breakers = (
            self.get_circuit_breakers()
        )

        ai_recovery = (
            self.get_ai_recovery_monitoring()
        )

        summary = (
            self.build_run_summary(
                runs
            )
        )

        circuit_breaker_summary = (
            self.build_circuit_breaker_summary(
                circuit_breakers
            )
        )

        job_health = (
            self.build_job_health(
                runs
            )
        )

        alerts = (
            self.build_health_alerts(

                summary=summary,

                circuit_breaker_summary=
                    circuit_breaker_summary,

                ai_recovery=
                    ai_recovery,
            )
        )

        health = (
            self.resolve_dashboard_health(

                summary=summary,

                circuit_breaker_summary=
                    circuit_breaker_summary,

                ai_recovery=
                    ai_recovery,
            )
        )

        return {

            "health":
                health,

            "generated_at":
                datetime.now(
                    timezone.utc
                ).isoformat(),

            "summary":
                summary,

            "job_health":
                job_health,

            "circuit_breaker_summary":
                circuit_breaker_summary,

            "ai_recovery_summary": {

                "recovery_queue_count":
                    ai_recovery[
                        "recovery_queue_count"
                    ],

                "dead_letter_count":
                    ai_recovery[
                        "dead_letter_count"
                    ],
            },

            "alerts":
                alerts,
        }

    def build_run_summary(
        self,
        runs: list[dict],
    ):

        total_runs = (
            len(runs)
        )

        completed_runs = (
            self.count_runs_by_status(
                runs,
                "COMPLETED",
            )
        )

        completed_with_errors = (
            self.count_runs_by_status(
                runs,
                "COMPLETED_WITH_ERRORS",
            )
        )

        failed_runs = (
            self.count_runs_by_status(
                runs,
                "FAILED",
            )
        )

        skipped_runs = (
            self.count_runs_by_status(
                runs,
                "SKIPPED",
            )
        )

        running_runs = (
            self.count_runs_by_status(
                runs,
                "RUNNING",
            )
        )

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

        healthy_runs = (
            completed_runs
            + skipped_runs
        )

        success_rate = (
            round(
                healthy_runs
                / total_runs
                * 100,
                1,
            )
            if total_runs
            else 100
        )

        error_rate = (
            round(
                error_count
                / processed_count
                * 100,
                1,
            )
            if processed_count
            else 0
        )

        return {

            "total_runs":
                total_runs,

            "completed_runs":
                completed_runs,

            "completed_with_errors":
                completed_with_errors,

            "failed_runs":
                failed_runs,

            "skipped_runs":
                skipped_runs,

            "running_runs":
                running_runs,

            "processed_count":
                processed_count,

            "error_count":
                error_count,

            "success_rate":
                success_rate,

            "error_rate":
                error_rate,
        }

    def build_job_health(
        self,
        runs: list[dict],
    ):

        grouped_runs: dict[str, list[dict]] = {}

        for run in runs:

            job_name = (
                run.get(
                    "job_name",
                    "unknown"
                )
            )

            grouped_runs.setdefault(
                job_name,
                []
            ).append(
                run
            )

        job_health = []

        for job_name, job_runs in grouped_runs.items():

            summary = (
                self.build_run_summary(
                    job_runs
                )
            )

            latest_run = (
                job_runs[0]
            )

            health = (
                self.resolve_job_health(
                    summary
                )
            )

            job_health.append({

                "job_name":
                    job_name,

                "health":
                    health,

                "last_status":
                    latest_run.get(
                        "status"
                    ),

                "last_started_at":
                    latest_run.get(
                        "started_at"
                    ),

                "last_completed_at":
                    latest_run.get(
                        "completed_at"
                    ),

                **summary,
            })

        return sorted(

            job_health,

            key=lambda job: (
                job.get(
                    "job_name"
                )
            ),
        )

    def build_circuit_breaker_summary(
        self,
        circuit_breakers: list[dict],
    ):

        return {

            "total":
                len(circuit_breakers),

            "open":
                self.count_breakers_by_state(
                    circuit_breakers,
                    "OPEN",
                ),

            "half_open":
                self.count_breakers_by_state(
                    circuit_breakers,
                    "HALF_OPEN",
                ),

            "closed":
                self.count_breakers_by_state(
                    circuit_breakers,
                    "CLOSED",
                ),
        }

    def build_health_alerts(
        self,
        summary: dict,
        circuit_breaker_summary: dict,
        ai_recovery: dict,
    ):

        alerts = []

        if summary["failed_runs"] > 0:

            alerts.append({
                "severity":
                    "CRITICAL",
                "title":
                    "Automation job failures",
                "description":
                    (
                        f"{summary['failed_runs']} "
                        "recent jobs failed"
                    ),
            })

        if summary["completed_with_errors"] > 0:

            alerts.append({
                "severity":
                    "WARNING",
                "title":
                    "Runs completed with errors",
                "description":
                    (
                        f"{summary['completed_with_errors']} "
                        "recent jobs completed with errors"
                    ),
            })

        if circuit_breaker_summary["open"] > 0:

            alerts.append({
                "severity":
                    "CRITICAL",
                "title":
                    "Open circuit breakers",
                "description":
                    (
                        f"{circuit_breaker_summary['open']} "
                        "breakers are open"
                    ),
            })

        if ai_recovery["dead_letter_count"] > 0:

            alerts.append({
                "severity":
                    "WARNING",
                "title":
                    "Dead-letter executions",
                "description":
                    (
                        f"{ai_recovery['dead_letter_count']} "
                        "AI executions need review"
                    ),
            })

        return alerts

    def resolve_dashboard_health(
        self,
        summary: dict,
        circuit_breaker_summary: dict,
        ai_recovery: dict,
    ):

        if (
            summary["failed_runs"] > 0
            or circuit_breaker_summary["open"] > 0
        ):

            return "CRITICAL"

        if (
            summary["completed_with_errors"] > 0
            or ai_recovery["dead_letter_count"] > 0
            or ai_recovery["recovery_queue_count"] > 0
            or circuit_breaker_summary["half_open"] > 0
        ):

            return "DEGRADED"

        return "HEALTHY"

    def resolve_job_health(
        self,
        summary: dict,
    ):

        if summary["failed_runs"] > 0:

            return "CRITICAL"

        if summary["completed_with_errors"] > 0:

            return "DEGRADED"

        return "HEALTHY"

    def count_runs_by_status(
        self,
        runs: list[dict],
        status: str,
    ):

        return len([

            run for run in runs

            if run.get(
                "status"
            ) == status
        ])

    def count_breakers_by_state(
        self,
        circuit_breakers: list[dict],
        state: str,
    ):

        return len([

            breaker for breaker in circuit_breakers

            if breaker.get(
                "state"
            ) == state
        ])

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
