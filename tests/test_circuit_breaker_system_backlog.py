from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

import app.main as main_module
from app.auth.jwt_service import JWTService
from app.main import app
from app.services.ai_provider_failover_service import AIProviderFailoverService
from app.services.circuit_breaker_dashboard_service import (
    CircuitBreakerDashboardService,
)
from app.services.circuit_breaker_reopen_service import (
    CircuitBreakerReopenService,
)
from app.services.circuit_breaker_service import CircuitBreakerService
from app.services.circuit_breaker_threshold_service import (
    CircuitBreakerThresholdService,
)
from app.services.dependency_health_monitoring_service import (
    DependencyHealthMonitoringService,
)
from app.services.outage_detection_service import OutageDetectionService
from app.services.provider_isolation_service import ProviderIsolationService
from app.services.service_degradation_service import ServiceDegradationService
from app.services.service_health_scoring_service import (
    ServiceHealthScoringService,
)
import app.dependencies as deps


class FakeCircuitBreakerRepository:
    def __init__(self, breakers: list[dict] | None = None):
        self.breakers = {
            item["breaker_key"]: dict(item)
            for item in (breakers or [])
        }

    def list_breakers(self):
        return list(self.breakers.values())

    def get_breaker(self, breaker_key: str):
        return self.breakers.get(breaker_key)

    def create_breaker(self, breaker):
        payload = breaker.model_dump(mode="json", exclude_none=True)
        self.breakers[payload["breaker_key"]] = payload
        return payload

    def update_breaker(self, breaker_key: str, data: dict):
        if breaker_key not in self.breakers:
            return
        self.breakers[breaker_key].update(data)

    def supports_half_open_success_count(self) -> bool:
        return True


def build_circuit_breaker_service(breakers: list[dict] | None = None):
    repository = FakeCircuitBreakerRepository(breakers)
    thresholds = CircuitBreakerThresholdService()
    return CircuitBreakerService(
        repository=repository,
        threshold_service=thresholds,
    ), repository, thresholds


def test_failure_thresholds_open_circuit_after_limit():
    service, repository, thresholds = build_circuit_breaker_service()
    thresholds.set_threshold("automation:demo", failure_threshold=2)

    service.allow_request("automation:demo")
    service.record_failure("automation:demo")
    service.record_failure("automation:demo")

    breaker = repository.get_breaker("automation:demo")
    assert breaker["state"] == "OPEN"
    assert breaker["failure_count"] == 2
    assert breaker["cooldown_until"] is not None


def test_automatic_reopen_transitions_to_half_open_after_cooldown():
    past = datetime.now(timezone.utc) - timedelta(minutes=1)
    service, repository, _ = build_circuit_breaker_service([
        {
            "id": "cb-1",
            "breaker_key": "automation:demo",
            "state": "OPEN",
            "failure_count": 5,
            "cooldown_until": past.isoformat(),
        }
    ])

    allowed = service.allow_request("automation:demo")

    assert allowed is True
    assert repository.get_breaker("automation:demo")["state"] == "HALF_OPEN"


def test_half_open_requires_success_threshold_before_closing():
    service, repository, thresholds = build_circuit_breaker_service([
        {
            "id": "cb-2",
            "breaker_key": "ai:openai",
            "state": "HALF_OPEN",
            "failure_count": 3,
            "half_open_success_count": 0,
        }
    ])
    thresholds.set_threshold("ai:openai", half_open_success_threshold=2)

    service.record_success("ai:openai")
    assert repository.get_breaker("ai:openai")["state"] == "HALF_OPEN"

    service.record_success("ai:openai")
    assert repository.get_breaker("ai:openai")["state"] == "CLOSED"


def test_service_degradation_mode_reflects_open_breakers():
    degradation = ServiceDegradationService()
    mode = degradation.get_degradation_mode([
        {"breaker_key": "ai:openai", "state": "OPEN"},
        {"breaker_key": "ai:anthropic", "state": "OPEN"},
        {"breaker_key": "automation:sla", "state": "OPEN"},
    ])

    assert mode["mode"] == "CRITICAL"
    assert "bulk_replay" in mode["features_disabled"]


def test_provider_isolation_tracks_open_ai_breakers():
    isolation = ProviderIsolationService()
    isolated = isolation.sync_from_breakers([
        {"breaker_key": "ai:openai", "state": "OPEN"},
        {"breaker_key": "ai:anthropic", "state": "CLOSED"},
    ])

    assert isolated == ["openai"]
    assert isolation.is_provider_isolated("openai") is True


def test_ai_provider_failover_skips_isolated_providers():
    isolation = ProviderIsolationService()
    isolation.isolate_provider("openai")
    failover = AIProviderFailoverService(isolation_service=isolation)
    failover.outage_handler.failure_threshold = 1

    selection = failover.select_available_provider(primary_provider="openai")

    assert selection["provider"] != "openai"
    assert selection["failover_used"] is True


def test_service_health_scoring_penalizes_open_breakers():
    scoring = ServiceHealthScoringService()
    overall = scoring.get_overall_health_score([
        {"breaker_key": "ai:openai", "state": "OPEN", "failure_count": 8},
        {"breaker_key": "automation:sla", "state": "CLOSED", "failure_count": 0},
    ])

    assert overall["score"] < 80
    assert overall["status"] in {"DEGRADED", "CRITICAL"}


def test_outage_detection_lists_active_open_breakers():
    detection = OutageDetectionService()
    summary = detection.get_outage_summary([
        {
            "breaker_key": "ai:gemini",
            "state": "OPEN",
            "failure_count": 6,
            "last_failure_at": datetime.now(timezone.utc).isoformat(),
        }
    ])

    assert summary["active_outage_count"] == 1
    assert summary["outages"][0]["service"] == "ai"


def test_dependency_health_monitoring_marks_unavailable_dependencies():
    monitoring = DependencyHealthMonitoringService()
    summary = monitoring.get_dependency_summary([
        {"breaker_key": "ai:openai", "state": "OPEN", "failure_count": 4},
    ])

    openai = next(
        item
        for item in summary["dependencies"]
        if item["dependency"] == "openai"
    )
    assert openai["status"] == "UNAVAILABLE"
    assert summary["unhealthy_count"] >= 1


def test_failure_analytics_and_dashboard_aggregate_views():
    service, _, thresholds = build_circuit_breaker_service([
        {
            "id": "cb-3",
            "breaker_key": "ai:openai",
            "state": "OPEN",
            "failure_count": 4,
            "cooldown_until": (
                datetime.now(timezone.utc) - timedelta(minutes=5)
            ).isoformat(),
        }
    ])
    reopen = CircuitBreakerReopenService(
        circuit_breaker_service=service,
        threshold_service=thresholds,
    )
    dashboard = CircuitBreakerDashboardService(
        circuit_breaker_service=service,
        threshold_service=thresholds,
        reopen_service=reopen,
    )

    view = dashboard.get_dashboard()

    assert view["breaker_count"] == 1
    assert "metrics" in view
    assert "analytics" in view
    assert view["degradation"]["mode"] in {"DEGRADED", "CRITICAL", "RECOVERING"}
    assert "health" in view
    assert view["outages"]["active_outage_count"] >= 0


def test_manual_reopen_forces_half_open_or_closed():
    service, repository, thresholds = build_circuit_breaker_service([
        {
            "id": "cb-4",
            "breaker_key": "automation:retry",
            "state": "OPEN",
            "failure_count": 5,
        }
    ])
    reopen = CircuitBreakerReopenService(
        circuit_breaker_service=service,
        threshold_service=thresholds,
    )

    half_open = reopen.manual_reopen("automation:retry")
    assert half_open["state"] == "HALF_OPEN"

    closed = reopen.manual_reopen(
        "automation:retry",
        force_closed=True,
    )
    assert closed["state"] == "CLOSED"
    assert repository.get_breaker("automation:retry")["state"] == "CLOSED"


def _auth_headers():
    token = JWTService().issue_access_token(
        user_id="user-1",
        org_id="org-1",
        role="ADMIN",
        token_id="circuit-breaker-tests",
    )
    return {"Authorization": f"Bearer {token}", "X-Organization-ID": "org-1"}


def test_circuit_breaker_api_endpoints(monkeypatch):
    service, _, thresholds = build_circuit_breaker_service([
        {
            "id": "cb-api",
            "breaker_key": "ai:openai",
            "state": "OPEN",
            "failure_count": 3,
        }
    ])
    dashboard = CircuitBreakerDashboardService(
        circuit_breaker_service=service,
        threshold_service=thresholds,
    )

    monkeypatch.setattr(deps, "circuit_breaker_service", service)
    monkeypatch.setattr(
        deps,
        "circuit_breaker_threshold_service",
        thresholds,
    )
    monkeypatch.setattr(
        deps,
        "circuit_breaker_reopen_service",
        CircuitBreakerReopenService(
            circuit_breaker_service=service,
            threshold_service=thresholds,
        ),
    )
    monkeypatch.setattr(
        deps,
        "circuit_breaker_dashboard_service",
        dashboard,
    )

    client = TestClient(app)
    headers = _auth_headers()

    dashboard_response = client.get(
        "/automation/circuit-breakers/dashboard",
        headers=headers,
    )
    metrics = client.get(
        "/automation/circuit-breakers/metrics",
        headers=headers,
    )
    degradation = client.get(
        "/automation/circuit-breakers/degradation",
        headers=headers,
    )
    health = client.get(
        "/automation/circuit-breakers/health-scores",
        headers=headers,
    )
    outages = client.get(
        "/automation/circuit-breakers/outages",
        headers=headers,
    )
    dependencies = client.get(
        "/automation/circuit-breakers/dependencies",
        headers=headers,
    )
    failover = client.get(
        "/automation/circuit-breakers/ai-failover",
        headers=headers,
    )
    set_threshold = client.post(
        "/automation/circuit-breakers/thresholds",
        json={
            "breaker_key": "ai:openai",
            "failure_threshold": 4,
            "cooldown_minutes": 8,
            "half_open_success_threshold": 2,
        },
        headers=headers,
    )

    assert dashboard_response.status_code == 200
    assert dashboard_response.json()["breaker_count"] == 1
    assert metrics.status_code == 200
    assert degradation.status_code == 200
    assert health.status_code == 200
    assert outages.status_code == 200
    assert dependencies.status_code == 200
    assert failover.status_code == 200
    assert set_threshold.status_code == 200
    assert set_threshold.json()["threshold"]["failure_threshold"] == 4
