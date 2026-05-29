from fastapi.testclient import TestClient

import app.main as main_module
from app.auth.jwt_service import JWTService
from app.main import app
from app.services.auto_recovery_rules_service import (
    AutoRecoveryRulesService,
)
from app.services.dead_letter_recovery_service import (
    DeadLetterRecoveryService,
)
from app.services.recovery_audit_service import (
    RecoveryAuditService,
)
from app.services.recovery_dashboard_service import (
    RecoveryDashboardService,
)
from app.services.recovery_orchestration_service import (
    RecoveryOrchestrationService,
)
from app.services.recovery_replay_tracking_service import (
    RecoveryReplayTrackingService,
)


class FakeDeadLetterRepository:
    def __init__(self, dead_letters: list[dict] | None = None):
        self.dead_letters = dead_letters or []
        self.updates = []

    def get_dead_letters(self, limit: int = 20):
        return self.dead_letters[:limit]

    def search_dead_letters(
        self,
        execution_type=None,
        failure_type=None,
        severity=None,
        project_id=None,
        query=None,
        limit: int = 50,
    ):
        results = list(self.dead_letters)
        if execution_type:
            results = [
                item
                for item in results
                if item.get("execution_type") == execution_type
            ]
        if failure_type:
            results = [
                item
                for item in results
                if item.get("failure_type") == failure_type
            ]
        if severity:
            results = [
                item
                for item in results
                if item.get("severity") == severity
            ]
        if project_id:
            results = [
                item
                for item in results
                if item.get("project_id") == project_id
            ]
        if query:
            needle = query.lower()
            results = [
                item
                for item in results
                if needle in str(item.get("id", "")).lower()
            ]
        return results[:limit]

    def get_by_id(self, log_id: str):
        for item in self.dead_letters:
            if item["id"] == log_id:
                return dict(item)
        return None

    def requeue_from_dead_letter(self, log_id: str):
        log = self.get_by_id(log_id)
        if not log:
            raise LookupError(f"Execution log '{log_id}' not found")
        log["dead_lettered"] = False
        log["status"] = "FAILED"
        log["retry_count"] = 0
        self.updates.append(("requeue", log_id))
        return log

    def mark_manual_recovered(self, log_id: str):
        log = self.get_by_id(log_id)
        if not log:
            raise LookupError(f"Execution log '{log_id}' not found")
        log["dead_lettered"] = False
        log["status"] = "RECOVERED"
        self.dead_letters = [
            item for item in self.dead_letters if item["id"] != log_id
        ]
        self.updates.append(("manual_recover", log_id))
        return log


class FakeRecoveryService:
    def retry_execution(self, log):
        log["retried"] = True


def build_service(dead_letters: list[dict] | None = None):
    repository = FakeDeadLetterRepository(dead_letters or [])
    audit = RecoveryAuditService()
    replay_tracking = RecoveryReplayTrackingService()
    return DeadLetterRecoveryService(
        repository=repository,
        recovery_service=FakeRecoveryService(),
        audit_service=audit,
        replay_tracking_service=replay_tracking,
    )


def test_replay_execution_flow_requeues_and_retries_dead_letter():
    service = build_service([
        {
            "id": "log-1",
            "dead_lettered": True,
            "execution_type": "PROJECT_PROCESSING",
            "failure_type": "TIMEOUT",
            "severity": "MEDIUM",
            "retry_count": 3,
        }
    ])

    result = service.replay_execution("log-1", initiated_by="alice")

    assert result["status"] == "REPLAYED"
    assert result["execution_log_id"] == "log-1"
    audits = service.list_audit_logs(execution_log_id="log-1")
    assert audits[0]["action"] == "REPLAY_EXECUTION"
    replays = service.list_replay_tracking(execution_log_id="log-1")
    assert replays[0]["status"] == "COMPLETED"


def test_manual_recovery_marks_log_recovered_and_audits():
    service = build_service([
        {
            "id": "log-2",
            "dead_lettered": True,
            "execution_type": "AI_ACTION_CREATED",
            "failure_type": "PERMISSION",
            "severity": "HIGH",
        }
    ])

    result = service.manual_recover("log-2", initiated_by="bob")

    assert result["status"] == "MANUALLY_RECOVERED"
    assert service.repository.get_by_id("log-2") is None
    audits = service.list_audit_logs(execution_log_id="log-2")
    assert audits[0]["action"] == "MANUAL_RECOVERY"


def test_dead_letter_search_and_filter():
    service = build_service([
        {
            "id": "alpha",
            "dead_lettered": True,
            "execution_type": "PROJECT_PROCESSING",
            "failure_type": "TIMEOUT",
            "severity": "MEDIUM",
            "project_id": "p-1",
        },
        {
            "id": "beta",
            "dead_lettered": True,
            "execution_type": "RISK_EVALUATION",
            "failure_type": "RATE_LIMIT",
            "severity": "LOW",
            "project_id": "p-2",
        },
    ])

    filtered = service.search_dead_letters(
        execution_type="PROJECT_PROCESSING",
        failure_type="TIMEOUT",
    )

    assert len(filtered) == 1
    assert filtered[0]["id"] == "alpha"


def test_dead_letter_retry_button_alias_replays_execution():
    service = build_service([
        {
            "id": "log-3",
            "dead_lettered": True,
            "execution_type": "PROJECT_PROCESSING",
            "failure_type": "TIMEOUT",
            "severity": "MEDIUM",
        }
    ])

    result = service.retry_dead_letter("log-3")

    assert result["status"] == "REPLAYED"


def test_recovery_metrics_and_analytics():
    service = build_service([
        {
            "id": "log-4",
            "dead_lettered": True,
            "execution_type": "PROJECT_PROCESSING",
            "failure_type": "TIMEOUT",
            "severity": "HIGH",
            "recovery_locked": True,
            "replayable": False,
        }
    ])

    metrics = service.get_metrics()
    analytics = service.get_analytics()

    assert metrics["dead_letter_count"] == 1
    assert metrics["by_failure_type"]["TIMEOUT"] == 1
    assert analytics["high_severity_count"] == 1
    assert analytics["locked_count"] == 1


def test_failure_categorization():
    service = build_service()

    result = service.categorize_failure("request timed out")

    assert result["failure_type"] == "TIMEOUT"
    assert result["replayable"] is True


def test_auto_recovery_rules_skip_permission_failures():
    rules = AutoRecoveryRulesService()
    decision = rules.evaluate({
        "failure_type": "PERMISSION",
        "severity": "HIGH",
        "retry_count": 0,
    })

    assert decision["matched"] is True
    assert decision["action"] == "SKIP"


def test_recovery_orchestration_retries_eligible_dead_letters():
    repository = FakeDeadLetterRepository([
        {
            "id": "log-5",
            "dead_lettered": True,
            "execution_type": "PROJECT_PROCESSING",
            "failure_type": "TIMEOUT",
            "severity": "MEDIUM",
            "retry_count": 1,
        },
        {
            "id": "log-6",
            "dead_lettered": True,
            "execution_type": "PROJECT_PROCESSING",
            "failure_type": "PERMISSION",
            "severity": "HIGH",
            "retry_count": 0,
        },
    ])
    recovery = DeadLetterRecoveryService(
        repository=repository,
        recovery_service=FakeRecoveryService(),
        audit_service=RecoveryAuditService(),
        replay_tracking_service=RecoveryReplayTrackingService(),
    )
    orchestration = RecoveryOrchestrationService(
        dead_letter_recovery_service=recovery,
    )

    result = orchestration.orchestrate_recovery_cycle(initiated_by="system")

    assert result["processed_count"] == 1
    assert result["skipped_count"] == 1


def test_recovery_dashboard_aggregates_recovery_views():
    service = build_service([
        {
            "id": "log-7",
            "dead_lettered": True,
            "execution_type": "PROJECT_PROCESSING",
            "failure_type": "TIMEOUT",
            "severity": "MEDIUM",
        }
    ])
    dashboard_service = RecoveryDashboardService(
        dead_letter_recovery_service=service,
    )

    dashboard = dashboard_service.get_dashboard()

    assert dashboard["dead_letter_count"] == 1
    assert "metrics" in dashboard
    assert "analytics" in dashboard
    assert "auto_recovery_rules" in dashboard


def test_recovery_replay_tracking_summary():
    tracking = RecoveryReplayTrackingService()
    replay = tracking.start_replay("log-8", "DEAD_LETTER_REPLAY", "alice")
    tracking.complete_replay(replay["id"], "COMPLETED")

    summary = tracking.get_summary()

    assert summary["total_replays"] == 1
    assert summary["completed"] == 1


def _auth_headers():
    token = JWTService().issue_access_token(
        user_id="user-1",
        org_id="org-1",
        role="ADMIN",
        token_id="dead-letter-tests",
    )
    return {"Authorization": f"Bearer {token}", "X-Organization-ID": "org-1"}


def test_dead_letter_recovery_api_endpoints(monkeypatch):
    service = build_service([
        {
            "id": "log-api",
            "dead_lettered": True,
            "execution_type": "PROJECT_PROCESSING",
            "failure_type": "RATE_LIMIT",
            "severity": "LOW",
        }
    ])
    dashboard_service = RecoveryDashboardService(
        dead_letter_recovery_service=service,
    )

    monkeypatch.setattr(
        main_module,
        "dead_letter_recovery_service",
        service,
    )
    monkeypatch.setattr(
        main_module,
        "recovery_dashboard_service",
        dashboard_service,
    )

    client = TestClient(app)
    headers = _auth_headers()

    dashboard = client.get(
        "/automation/dead-letters/dashboard",
        headers=headers,
    )
    metrics = client.get(
        "/automation/dead-letters/metrics",
        headers=headers,
    )
    analytics = client.get(
        "/automation/dead-letters/analytics",
        headers=headers,
    )
    rules = client.get(
        "/automation/dead-letters/auto-recovery-rules",
        headers=headers,
    )
    categorize = client.post(
        "/automation/dead-letters/categorize-failure",
        json={"error_message": "rate limit exceeded 429"},
        headers=headers,
    )

    assert dashboard.status_code == 200
    assert dashboard.json()["dead_letter_count"] == 1
    assert metrics.status_code == 200
    assert analytics.status_code == 200
    assert rules.status_code == 200
    assert categorize.status_code == 200
    assert categorize.json()["failure_type"] == "RATE_LIMIT"
