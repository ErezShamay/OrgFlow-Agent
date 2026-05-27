from app.repositories.ai_execution_log_repository import (
    AIExecutionLogRepository
)

from app.services.ai_retry_strategy_service import (
    AIRetryStrategyService
)

from app.repositories.project_repository import (
    ProjectRepository
)

from app.services.ai_automation_service import (
    AIAutomationService
)


class AIRecoveryService:

    def __init__(self):

        self.repository = (
            AIExecutionLogRepository()
        )

        self.retry_strategy_service = (
            AIRetryStrategyService()
        )

        self.project_repository = (
            ProjectRepository()
        )

        self.ai_automation_service = (
            AIAutomationService()
        )

        # ======================================
        # THROUGHPUT GOVERNANCE
        # ======================================

        self.max_recovery_per_cycle = 25

    # ==========================================
    # RUN RECOVERY CYCLE
    # ==========================================

    def run_recovery_cycle(
        self,
    ):

        print(
            "[AI_RECOVERY] "
            "Starting recovery cycle"
        )

        failed_logs = (
            self.repository
            .get_failed_executions()
        )

        # ======================================
        # RECOVERY BATCH LIMIT
        # ======================================

        failed_logs = (
            failed_logs[
                :self.max_recovery_per_cycle
            ]
        )

        print(
            f"[AI_RECOVERY] "
            f"Failed executions: "
            f"{len(failed_logs)}"
        )

        print(

            "[AI_RECOVERY] "

            f"Recovery batch size: "
            f"{len(failed_logs)} / "
            f"{self.max_recovery_per_cycle}"
        )

        # ======================================
        # NO FAILED EXECUTIONS
        # ======================================

        if not failed_logs:

            print(
                "[AI_RECOVERY] "
                "No failed executions"
            )

            return

        # ======================================
        # PROCESS FAILED EXECUTIONS
        # ======================================

        for log in failed_logs:

            try:

                self.retry_execution(
                    log
                )

            except Exception as error:

                print(
                    "[AI_RECOVERY] "
                    "Retry failed:",
                    str(error),
                )

        print(
            "[AI_RECOVERY] "
            "Recovery cycle completed"
        )

    # ==========================================
    # RETRY EXECUTION
    # ==========================================

    def retry_execution(
        self,
        log: dict,
    ):

        # ======================================
        # LOCK RECOVERY
        # ======================================

        self.repository.lock_recovery(
            log["id"]
        )

        try:

            retry_count = (
                log.get(
                    "retry_count",
                    0
                )
            )

            replayable = (
                log.get(
                    "replayable",
                    True
                )
            )

            execution_type = (
                log.get(
                    "execution_type"
                )
            )

            failure_type = (
                log.get(
                    "failure_type",
                    "UNKNOWN"
                )
            )

            # ==================================
            # REPLAYABLE CHECK
            # ==================================

            if not replayable:

                print(
                    "[AI_RECOVERY] "
                    "Execution not replayable"
                )

                return

            # ==================================
            # DEAD LETTER CHECK
            # ==================================

            if retry_count >= 3:

                print(
                    "[AI_RECOVERY] "
                    "Moving execution to dead-letter queue:",
                    log["id"],
                )

                self.repository.mark_dead_letter(
                    log["id"]
                )

                return

            # ==================================
            # CALCULATE NEXT RETRY
            # ==================================

            next_retry_at = (
                self.retry_strategy_service
                .calculate_next_retry(

                    failure_type=
                        failure_type,

                    retry_count=
                        retry_count + 1,
                )
            )

            # ==================================
            # RETRY EXECUTION
            # ==================================

            print(

                "[AI_RECOVERY] "

                f"Retrying execution: "
                f"{log['id']} "
                f"(attempt {retry_count + 1})"
            )

            print(

                "[AI_RECOVERY] "

                f"Replaying execution type: "
                f"{execution_type}"
            )

            print(

                "[AI_RECOVERY] "

                f"Failure type: "
                f"{failure_type}"
            )

            print(

                "[AI_RECOVERY] "

                f"Next retry scheduled at: "
                f"{next_retry_at.isoformat()}"
            )

            # ==================================
            # EXECUTION TYPE ROUTING
            # ==================================

            recovered = False

            if execution_type == "PROJECT_PROCESSING":

                recovered = (
                    self.replay_project_processing(
                        log
                    )
                )

            elif execution_type == "AI_ACTION_CREATED":

                recovered = (
                    self.replay_ai_action(
                        log
                    )
                )

            elif execution_type == "RISK_EVALUATION":

                recovered = (
                    self.replay_risk_evaluation(
                        log
                    )
                )

            elif execution_type == "AUTO_EXECUTION_SKIPPED":

                recovered = (
                    self.replay_auto_execution_skip(
                        log
                    )
                )

            elif execution_type == "FINGERPRINT_BLOCKED":

                recovered = (
                    self.replay_fingerprint_block(
                        log
                    )
                )

            elif execution_type == "DUPLICATE_ACTION_BLOCKED":

                recovered = (
                    self.replay_duplicate_block(
                        log
                    )
                )

            else:

                print(

                    "[AI_RECOVERY] "

                    f"No replay handler for: "
                    f"{execution_type}"
                )

            # ==================================
            # UPDATE RETRY COUNT
            # ==================================

            self.repository.update_retry(

                log_id=
                    log["id"],

                retry_count=
                    retry_count + 1,

                next_retry_at=
                    next_retry_at,
            )

            if recovered:

                self.repository.mark_recovered(
                    log["id"]
                )

                print(

                    "[AI_RECOVERY] "

                    f"Execution recovered: "
                    f"{log['id']}"
                )

                return

            print(

                "[AI_RECOVERY] "

                f"Execution completed: "
                f"{log['id']}"
            )

        finally:

            # ==================================
            # UNLOCK RECOVERY
            # ==================================

            self.repository.unlock_recovery(
                log["id"]
            )

    # ==========================================
    # REPLAY PROJECT PROCESSING
    # ==========================================

    def replay_project_processing(
        self,
        log: dict,
    ):

        project_id = (
            log.get(
                "project_id"
            )
        )

        if not project_id:

            print(
                "[AI_RECOVERY] "
                "Cannot replay project processing "
                "without project_id"
            )

            return False

        project = (
            self.project_repository
            .get_project_by_id(
                project_id
            )
        )

        if not project:

            print(
                "[AI_RECOVERY] "
                "Project not found for replay:",
                project_id,
            )

            return False

        print(
            "[AI_RECOVERY] "
            "Replaying project processing:",
            project_id,
        )

        self.ai_automation_service.process_project(
            project
        )

        return True

    # ==========================================
    # REPLAY AI ACTION
    # ==========================================

    def replay_ai_action(
        self,
        log: dict,
    ):

        print(
            "[AI_RECOVERY] "
            "Replaying AI action"
        )

        # Future orchestration replay logic

        return False

    # ==========================================
    # REPLAY RISK EVALUATION
    # ==========================================

    def replay_risk_evaluation(
        self,
        log: dict,
    ):

        print(
            "[AI_RECOVERY] "
            "Replaying risk evaluation"
        )

        return self.replay_project_processing(
            log
        )

    # ==========================================
    # REPLAY AUTO EXECUTION SKIP
    # ==========================================

    def replay_auto_execution_skip(
        self,
        log: dict,
    ):

        print(
            "[AI_RECOVERY] "
            "Replaying skipped execution"
        )

        # Future governance replay logic

        return False

    # ==========================================
    # REPLAY FINGERPRINT BLOCK
    # ==========================================

    def replay_fingerprint_block(
        self,
        log: dict,
    ):

        print(
            "[AI_RECOVERY] "
            "Replaying fingerprint block"
        )

        # Future fingerprint replay logic

        return False

    # ==========================================
    # REPLAY DUPLICATE BLOCK
    # ==========================================

    def replay_duplicate_block(
        self,
        log: dict,
    ):

        print(
            "[AI_RECOVERY] "
            "Replaying duplicate block"
        )

        # Future duplicate resolution logic

        return False
