from fastapi.testclient import TestClient

import app.main as main_module
from app.auth.jwt_service import JWTService
from app.main import app
from app.services.ai_metrics_service import AiMetricsService
from app.services.automation_metrics_service import AutomationMetricsService
from app.services.centralized_logging_service import CentralizedLoggingService
from app.services.crash_reporting_service import CrashReportingService
from app.services.distributed_tracing_service import DistributedTracingService
from app.services.grafana_dashboards_service import GrafanaDashboardsService
from app.services.metrics_collection_service import MetricsCollectionService
from app.services.observability_alerting_service import ObservabilityAlertingService
from app.services.observability_dashboard_service import ObservabilityDashboardService
from app.services.performance_monitoring_service import PerformanceMonitoringService
from app.services.prometheus_integration_service import PrometheusIntegrationService
from app.services.runtime_diagnostics_service import RuntimeDiagnosticsService
from app.services.sentry_integration_service import SentryIntegrationService
from app.services.sla_metrics_service import SlaMetricsService
import app.dependencies as deps


def build_dashboard():
    return ObservabilityDashboardService()


def test_centralized_logging():
    service = CentralizedLoggingService()
    config = service.get_config()
    assert config["provider"] == "structured_json"
    assert config["aggregation"] == "loki"

    streams = service.get_log_streams()
    assert streams["total"] >= 4

    results = service.search_logs(query="Request", level="INFO")
    assert results["total"] >= 1
    assert service.validate_setup()["valid"] is True


def test_metrics_collection():
    service = MetricsCollectionService()
    catalog = service.get_catalog()
    assert catalog["total"] >= 5

    snapshot = service.record_snapshot(
        requests_total=100,
        active_connections=5,
        memory_bytes=50_000_000,
    )
    assert snapshot["http_requests_total"] == 100
    assert service.validate_setup()["valid"] is True


def test_prometheus_integration():
    service = PrometheusIntegrationService()
    config = service.get_config()
    assert config["scrape_interval_seconds"] == 15

    validation = service.validate_integration()
    assert validation["valid"] is True
    assert "api:8000" in validation["targets_found"]

    targets = service.get_scrape_targets()
    assert targets["total"] >= 2


def test_grafana_dashboards():
    service = GrafanaDashboardsService()
    dashboards = service.list_dashboards()
    assert dashboards["total"] >= 3

    overview = service.get_dashboard("orgflow-overview")
    assert overview["found"] is True
    assert overview["file_exists"] is True

    validation = service.validate_provisioning()
    assert validation["valid"] is True
    assert "orgflow-overview" in validation["dashboards_found"]


def test_ai_metrics():
    service = AiMetricsService()
    catalog = service.get_metrics_catalog()
    assert catalog["total"] >= 5

    snapshot = service.get_snapshot(
        tokens_used=1500,
        avg_latency_ms=450.0,
        error_rate=0.5,
    )
    assert snapshot["tokens_used_total"] == 1500
    assert service.validate_setup()["valid"] is True


def test_automation_metrics():
    service = AutomationMetricsService()
    catalog = service.get_metrics_catalog()
    assert catalog["total"] >= 5

    snapshot = service.get_snapshot(
        jobs_processed=42,
        queue_depth=3,
        success_rate=98.5,
    )
    assert snapshot["jobs_processed_total"] == 42
    assert service.validate_setup()["valid"] is True


def test_sla_metrics():
    service = SlaMetricsService()
    targets = service.get_targets()
    assert targets["total"] >= 4

    evaluation = service.evaluate_sla(
        metric="api_availability",
        actual_value=99.95,
    )
    assert evaluation["met"] is True

    summary = service.get_compliance_summary()
    assert summary["compliant"] is True
    assert service.validate_setup()["valid"] is True


def test_distributed_tracing():
    service = DistributedTracingService()
    config = service.get_config()
    assert config["enabled"] is True
    assert "X-Trace-ID" in config["headers"]

    context = service.create_span_context(trace_id="trace-abc123")
    assert context["trace_id"] == "trace-abc123"

    headers = service.validate_trace_headers({"X-Trace-ID": "trace-abc123"})
    assert headers["valid"] is True
    assert service.validate_setup()["valid"] is True


def test_observability_alerting():
    service = ObservabilityAlertingService()
    rules = service.list_rules()
    assert rules["total"] >= 5

    firing = service.evaluate_rule(
        rule_id="HIGH_ERROR_RATE",
        current_value=10.0,
    )
    assert firing["firing"] is True

    clear = service.evaluate_rule(
        rule_id="HIGH_ERROR_RATE",
        current_value=1.0,
    )
    assert clear["firing"] is False
    assert service.validate_setup()["valid"] is True


def test_crash_reporting():
    service = CrashReportingService()
    config = service.get_config()
    assert config["capture_unhandled_exceptions"] is True

    crash = service.capture_crash(
        error_type="ValueError",
        message="Invalid input",
        stack_trace="Traceback...",
        trace_id="trace-123",
    )
    assert crash["captured"] is True
    assert crash["trace_id"] == "trace-123"
    assert service.validate_setup()["valid"] is True


def test_sentry_integration():
    service = SentryIntegrationService()
    config = service.get_config()
    assert config["enabled"] is True
    assert "fastapi" in config["integrations"]

    checklist = service.get_init_checklist()
    assert checklist["total"] >= 4

    event = service.simulate_event(level="error", message="Test")
    assert event["sent"] is True
    assert service.validate_setup()["valid"] is True


def test_runtime_diagnostics():
    service = RuntimeDiagnosticsService()
    snapshot = service.get_snapshot()
    assert "python_version" in snapshot
    assert snapshot["pid"] > 0

    health = service.get_health_indicators()
    assert health["healthy"] is True
    assert service.validate_setup()["valid"] is True


def test_performance_monitoring():
    service = PerformanceMonitoringService()
    healthy = service.evaluate_performance(
        p50_ms=100.0,
        p95_ms=500.0,
        p99_ms=1500.0,
        error_rate=0.5,
        throughput_rps=50.0,
    )
    assert healthy["healthy"] is True

    degraded = service.evaluate_performance(
        p50_ms=300.0,
        p95_ms=1200.0,
        p99_ms=3000.0,
        error_rate=5.0,
        throughput_rps=2.0,
    )
    assert degraded["healthy"] is False

    summary = service.get_endpoint_summary()
    assert summary["total"] >= 3
    assert service.validate_setup()["valid"] is True


def test_observability_dashboard_aggregates_all_domains():
    dashboard = build_dashboard()
    result = dashboard.get_dashboard()

    assert result["observable"] is True
    assert result["logging"]["provider"] == "structured_json"
    assert result["prometheus"]["valid"] is True
    assert result["sla"]["compliant"] is True
    assert result["runtime"]["healthy"] is True


def _auth_headers():
    token = JWTService().issue_access_token(
        user_id="user-1",
        org_id="org-1",
        role="ADMIN",
        token_id="observability-backlog-tests",
    )
    return {"Authorization": f"Bearer {token}", "X-Organization-ID": "org-1"}


def test_observability_api_endpoints(monkeypatch):
    dashboard = build_dashboard()
    monkeypatch.setattr(
        deps,
        "observability_dashboard_service",
        dashboard,
    )

    client = TestClient(app)
    headers = _auth_headers()

    get_endpoints = [
        "/observability/dashboard",
        "/observability/logging/config",
        "/observability/logging/streams",
        "/observability/logging/search",
        "/observability/logging/validate",
        "/observability/metrics/config",
        "/observability/metrics/catalog",
        "/observability/metrics/snapshot",
        "/observability/metrics/validate",
        "/observability/prometheus/config",
        "/observability/prometheus/validate",
        "/observability/prometheus/targets",
        "/observability/grafana/config",
        "/observability/grafana/dashboards",
        "/observability/grafana/dashboards/orgflow-overview",
        "/observability/grafana/validate",
        "/observability/ai-metrics/config",
        "/observability/ai-metrics/catalog",
        "/observability/ai-metrics/snapshot",
        "/observability/ai-metrics/validate",
        "/observability/automation-metrics/config",
        "/observability/automation-metrics/catalog",
        "/observability/automation-metrics/snapshot",
        "/observability/automation-metrics/validate",
        "/observability/sla/targets",
        "/observability/sla/evaluate",
        "/observability/sla/compliance",
        "/observability/sla/validate",
        "/observability/tracing/config",
        "/observability/tracing/validate",
        "/observability/alerting/config",
        "/observability/alerting/rules",
        "/observability/alerting/evaluate",
        "/observability/alerting/validate",
        "/observability/crashes/config",
        "/observability/crashes/recent",
        "/observability/crashes/validate",
        "/observability/sentry/config",
        "/observability/sentry/checklist",
        "/observability/sentry/validate",
        "/observability/runtime/snapshot",
        "/observability/runtime/health",
        "/observability/runtime/validate",
        "/observability/performance/config",
        "/observability/performance/evaluate",
        "/observability/performance/summary",
        "/observability/performance/validate",
    ]

    for path in get_endpoints:
        response = client.get(path, headers=headers)
        assert response.status_code == 200, path

    dashboard_response = client.get(
        "/observability/dashboard",
        headers=headers,
    ).json()
    assert dashboard_response["observable"] is True
