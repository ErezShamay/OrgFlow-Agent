from app.services.auto_recovery_rules_service import (
    AutoRecoveryRulesService,
)
from app.services.dead_letter_recovery_service import (
    DeadLetterRecoveryService,
)
from app.services.recovery_orchestration_service import (
    RecoveryOrchestrationService,
)


class RecoveryDashboardService:
    def __init__(
        self,
        dead_letter_recovery_service: DeadLetterRecoveryService | None = None,
        recovery_orchestration_service: RecoveryOrchestrationService | None = None,
        auto_recovery_rules_service: AutoRecoveryRulesService | None = None,
    ):
        self.dead_letter_recovery_service = (
            dead_letter_recovery_service
            or DeadLetterRecoveryService()
        )
        self.recovery_orchestration_service = (
            recovery_orchestration_service
            or RecoveryOrchestrationService(
                dead_letter_recovery_service=self.dead_letter_recovery_service,
            )
        )
        self.auto_recovery_rules_service = (
            auto_recovery_rules_service
            or AutoRecoveryRulesService()
        )

    def get_dashboard(
        self,
        dead_letter_limit: int = 50,
    ):
        dead_letters = (
            self.dead_letter_recovery_service
            .search_dead_letters(limit=dead_letter_limit)
        )
        metrics = self.dead_letter_recovery_service.get_metrics()
        analytics = self.dead_letter_recovery_service.get_analytics()
        audit_logs = (
            self.dead_letter_recovery_service
            .list_audit_logs(limit=25)
        )
        replay_tracking = (
            self.dead_letter_recovery_service
            .list_replay_tracking(limit=25)
        )

        return {
            "dead_letters": dead_letters,
            "dead_letter_count": len(dead_letters),
            "metrics": metrics,
            "analytics": analytics,
            "audit_logs": audit_logs,
            "replay_tracking": replay_tracking,
            "auto_recovery_rules": (
                self.auto_recovery_rules_service.list_rules()
            ),
        }
