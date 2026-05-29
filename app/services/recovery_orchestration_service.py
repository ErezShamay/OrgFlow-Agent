from app.services.auto_recovery_rules_service import (
    AutoRecoveryRulesService,
)
from app.services.dead_letter_recovery_service import (
    DeadLetterRecoveryService,
)


class RecoveryOrchestrationService:
    def __init__(
        self,
        dead_letter_recovery_service: DeadLetterRecoveryService | None = None,
        auto_recovery_rules_service: AutoRecoveryRulesService | None = None,
    ):
        self.dead_letter_recovery_service = (
            dead_letter_recovery_service
            or DeadLetterRecoveryService()
        )
        self.auto_recovery_rules_service = (
            auto_recovery_rules_service
            or AutoRecoveryRulesService()
        )

    def orchestrate_recovery_cycle(
        self,
        initiated_by: str = "system",
        limit: int = 25,
    ):
        dead_letters = (
            self.dead_letter_recovery_service
            .search_dead_letters(limit=limit)
        )

        processed = []
        skipped = []

        for log in dead_letters:
            decision = (
                self.auto_recovery_rules_service
                .evaluate(log)
            )

            if decision["action"] == "SKIP":
                skipped.append({
                    "execution_log_id": log["id"],
                    "rule_id": decision["rule_id"],
                    "reason": "AUTO_RULE_SKIP",
                })
                continue

            if decision["action"] != "RETRY":
                skipped.append({
                    "execution_log_id": log["id"],
                    "rule_id": decision.get("rule_id"),
                    "reason": decision["action"],
                })
                continue

            result = (
                self.dead_letter_recovery_service
                .replay_execution(
                    log_id=log["id"],
                    initiated_by=initiated_by,
                )
            )
            processed.append(result)

        return {
            "processed_count": len(processed),
            "skipped_count": len(skipped),
            "processed": processed,
            "skipped": skipped,
        }
