from app.repositories.ai_execution_log_repository import (
    AIExecutionLogRepository,
)
from app.services.ai_failure_classification_service import (
    AIFailureClassificationService,
)
from app.services.ai_recovery_service import (
    AIRecoveryService,
)
from app.services.recovery_audit_service import (
    RecoveryAuditService,
)
from app.services.recovery_replay_tracking_service import (
    RecoveryReplayTrackingService,
)


class DeadLetterRecoveryService:
    def __init__(
        self,
        repository: AIExecutionLogRepository | None = None,
        recovery_service: AIRecoveryService | None = None,
        audit_service: RecoveryAuditService | None = None,
        replay_tracking_service: RecoveryReplayTrackingService | None = None,
        failure_classification_service: AIFailureClassificationService | None = None,
    ):
        self.repository = repository or AIExecutionLogRepository()
        self.recovery_service = recovery_service or AIRecoveryService()
        self.audit_service = audit_service or RecoveryAuditService()
        self.replay_tracking_service = (
            replay_tracking_service
            or RecoveryReplayTrackingService()
        )
        self.failure_classification_service = (
            failure_classification_service
            or AIFailureClassificationService()
        )

    def search_dead_letters(
        self,
        execution_type: str | None = None,
        failure_type: str | None = None,
        severity: str | None = None,
        project_id: str | None = None,
        query: str | None = None,
        limit: int = 50,
    ):
        return self.repository.search_dead_letters(
            execution_type=execution_type,
            failure_type=failure_type,
            severity=severity,
            project_id=project_id,
            query=query,
            limit=limit,
        )

    def categorize_failure(
        self,
        error_message: str,
    ):
        class SyntheticError(Exception):
            pass

        error = SyntheticError(error_message)
        return self.failure_classification_service.classify_failure(error)

    def replay_execution(
        self,
        log_id: str,
        initiated_by: str = "operator",
    ):
        log = self.repository.get_by_id(log_id)
        if not log:
            raise LookupError(f"Execution log '{log_id}' not found")
        if not log.get("dead_lettered"):
            raise ValueError(
                f"Execution '{log_id}' is not in the dead-letter queue"
            )

        replay = self.replay_tracking_service.start_replay(
            execution_log_id=log_id,
            replay_type="DEAD_LETTER_REPLAY",
            initiated_by=initiated_by,
        )

        try:
            requeued = self.repository.requeue_from_dead_letter(log_id)
            self.recovery_service.retry_execution(requeued)

            self.audit_service.record(
                action="REPLAY_EXECUTION",
                execution_log_id=log_id,
                initiated_by=initiated_by,
                outcome="COMPLETED",
                metadata={"replay_id": replay["id"]},
            )

            self.replay_tracking_service.complete_replay(
                replay_id=replay["id"],
                status="COMPLETED",
            )

            return {
                "status": "REPLAYED",
                "execution_log_id": log_id,
                "replay_id": replay["id"],
                "initiated_by": initiated_by,
            }

        except Exception as error:
            self.replay_tracking_service.complete_replay(
                replay_id=replay["id"],
                status="FAILED",
                error=str(error),
            )
            self.audit_service.record(
                action="REPLAY_EXECUTION",
                execution_log_id=log_id,
                initiated_by=initiated_by,
                outcome="FAILED",
                metadata={"error": str(error)},
            )
            raise

    def manual_recover(
        self,
        log_id: str,
        initiated_by: str = "operator",
    ):
        log = self.repository.get_by_id(log_id)
        if not log:
            raise LookupError(f"Execution log '{log_id}' not found")
        if not log.get("dead_lettered"):
            raise ValueError(
                f"Execution '{log_id}' is not in the dead-letter queue"
            )

        updated = self.repository.mark_manual_recovered(log_id)

        self.audit_service.record(
            action="MANUAL_RECOVERY",
            execution_log_id=log_id,
            initiated_by=initiated_by,
            outcome="COMPLETED",
        )

        return {
            "status": "MANUALLY_RECOVERED",
            "execution_log_id": log_id,
            "log": updated,
        }

    def retry_dead_letter(
        self,
        log_id: str,
        initiated_by: str = "operator",
    ):
        return self.replay_execution(
            log_id=log_id,
            initiated_by=initiated_by,
        )

    def get_metrics(self):
        dead_letters = self.repository.get_dead_letters(limit=500)
        by_failure_type = {}
        by_severity = {}
        by_execution_type = {}

        for item in dead_letters:
            failure = item.get("failure_type") or "UNKNOWN"
            severity = item.get("severity") or "UNKNOWN"
            execution_type = item.get("execution_type") or "UNKNOWN"
            by_failure_type[failure] = by_failure_type.get(failure, 0) + 1
            by_severity[severity] = by_severity.get(severity, 0) + 1
            by_execution_type[execution_type] = (
                by_execution_type.get(execution_type, 0) + 1
            )

        replay_summary = self.replay_tracking_service.get_summary()
        audit_entries = self.audit_service.list_entries(limit=500)

        return {
            "dead_letter_count": len(dead_letters),
            "by_failure_type": by_failure_type,
            "by_severity": by_severity,
            "by_execution_type": by_execution_type,
            "replay_summary": replay_summary,
            "audit_event_count": len(audit_entries),
        }

    def get_analytics(self):
        metrics = self.get_metrics()
        dead_letters = self.repository.get_dead_letters(limit=500)

        locked_count = len(
            [
                item
                for item in dead_letters
                if item.get("recovery_locked")
            ]
        )
        high_severity_count = len(
            [
                item
                for item in dead_letters
                if item.get("severity") == "HIGH"
            ]
        )
        replayable_count = len(
            [
                item
                for item in dead_letters
                if item.get("replayable", True)
            ]
        )

        return {
            "summary": metrics,
            "locked_count": locked_count,
            "high_severity_count": high_severity_count,
            "replayable_count": replayable_count,
            "non_replayable_count": len(dead_letters) - replayable_count,
        }

    def list_audit_logs(
        self,
        execution_log_id: str | None = None,
        limit: int = 100,
    ):
        return self.audit_service.list_entries(
            execution_log_id=execution_log_id,
            limit=limit,
        )

    def list_replay_tracking(
        self,
        execution_log_id: str | None = None,
        limit: int = 100,
    ):
        return self.replay_tracking_service.list_replays(
            execution_log_id=execution_log_id,
            limit=limit,
        )
