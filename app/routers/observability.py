"""Observability routes.

Extracted from app/main.py during the 2026-07 architecture-modularization
refactor. Shared service singletons live in app/dependencies.py; shared
request models live in app/schemas/api_requests.py.
"""
from __future__ import annotations


from fastapi import APIRouter
import app.dependencies as deps


router = APIRouter()


@router.get("/observability/dashboard")
def get_observability_dashboard():
    return deps.observability_dashboard_service.get_dashboard()


@router.get("/observability/logging/config")
def get_observability_logging_config():
    return deps.observability_dashboard_service.get_logging_config()


@router.get("/observability/logging/streams")
def get_observability_log_streams():
    return deps.observability_dashboard_service.get_log_streams()


@router.get("/observability/logging/search")
def search_observability_logs(
    query: str = "",
    level: str | None = None,
    limit: int = 100,
):
    return deps.observability_dashboard_service.search_logs(
        query=query,
        level=level,
        limit=limit,
    )


@router.get("/observability/logging/validate")
def validate_observability_logging():
    return deps.observability_dashboard_service.validate_logging()


@router.get("/observability/metrics/config")
def get_observability_metrics_config():
    return deps.observability_dashboard_service.get_metrics_config()


@router.get("/observability/metrics/catalog")
def get_observability_metrics_catalog():
    return deps.observability_dashboard_service.get_metrics_catalog()


@router.get("/observability/metrics/snapshot")
def get_observability_metrics_snapshot(
    requests_total: int = 0,
    active_connections: int = 0,
    memory_bytes: int = 0,
):
    return deps.observability_dashboard_service.get_metrics_snapshot(
        requests_total=requests_total,
        active_connections=active_connections,
        memory_bytes=memory_bytes,
    )


@router.get("/observability/metrics/validate")
def validate_observability_metrics():
    return deps.observability_dashboard_service.validate_metrics()


@router.get("/observability/prometheus/config")
def get_observability_prometheus_config():
    return deps.observability_dashboard_service.get_prometheus_config()


@router.get("/observability/prometheus/validate")
def validate_observability_prometheus():
    return deps.observability_dashboard_service.validate_prometheus()


@router.get("/observability/prometheus/targets")
def get_observability_prometheus_targets():
    return deps.observability_dashboard_service.get_prometheus_targets()


@router.get("/observability/grafana/config")
def get_observability_grafana_config():
    return deps.observability_dashboard_service.get_grafana_config()


@router.get("/observability/grafana/dashboards")
def list_observability_grafana_dashboards():
    return deps.observability_dashboard_service.list_grafana_dashboards()


@router.get("/observability/grafana/dashboards/{uid}")
def get_observability_grafana_dashboard(uid: str):
    return deps.observability_dashboard_service.get_grafana_dashboard(uid)


@router.get("/observability/grafana/validate")
def validate_observability_grafana():
    return deps.observability_dashboard_service.validate_grafana()


@router.get("/observability/ai-metrics/config")
def get_observability_ai_metrics_config():
    return deps.observability_dashboard_service.get_ai_metrics_config()


@router.get("/observability/ai-metrics/catalog")
def get_observability_ai_metrics_catalog():
    return deps.observability_dashboard_service.get_ai_metrics_catalog()


@router.get("/observability/ai-metrics/snapshot")
def get_observability_ai_metrics_snapshot(
    tokens_used: int = 0,
    avg_latency_ms: float = 0.0,
    error_rate: float = 0.0,
):
    return deps.observability_dashboard_service.get_ai_metrics_snapshot(
        tokens_used=tokens_used,
        avg_latency_ms=avg_latency_ms,
        error_rate=error_rate,
    )


@router.get("/observability/ai-metrics/validate")
def validate_observability_ai_metrics():
    return deps.observability_dashboard_service.validate_ai_metrics()


@router.get("/observability/automation-metrics/config")
def get_observability_automation_metrics_config():
    return deps.observability_dashboard_service.get_automation_metrics_config()


@router.get("/observability/automation-metrics/catalog")
def get_observability_automation_metrics_catalog():
    return deps.observability_dashboard_service.get_automation_metrics_catalog()


@router.get("/observability/automation-metrics/snapshot")
def get_observability_automation_metrics_snapshot(
    jobs_processed: int = 0,
    queue_depth: int = 0,
    success_rate: float = 100.0,
):
    return deps.observability_dashboard_service.get_automation_metrics_snapshot(
        jobs_processed=jobs_processed,
        queue_depth=queue_depth,
        success_rate=success_rate,
    )


@router.get("/observability/automation-metrics/validate")
def validate_observability_automation_metrics():
    return deps.observability_dashboard_service.validate_automation_metrics()


@router.get("/observability/sla/targets")
def get_observability_sla_targets():
    return deps.observability_dashboard_service.get_sla_targets()


@router.get("/observability/sla/evaluate")
def evaluate_observability_sla(
    metric: str = "api_availability",
    actual_value: float = 99.95,
):
    return deps.observability_dashboard_service.evaluate_sla(
        metric=metric,
        actual_value=actual_value,
    )


@router.get("/observability/sla/compliance")
def get_observability_sla_compliance():
    return deps.observability_dashboard_service.get_sla_compliance()


@router.get("/observability/sla/validate")
def validate_observability_sla_metrics():
    return deps.observability_dashboard_service.validate_sla_metrics()


@router.get("/observability/tracing/config")
def get_observability_tracing_config():
    return deps.observability_dashboard_service.get_tracing_config()


@router.get("/observability/tracing/validate")
def validate_observability_tracing():
    return deps.observability_dashboard_service.validate_tracing()


@router.get("/observability/alerting/config")
def get_observability_alerting_config():
    return deps.observability_dashboard_service.get_alerting_config()


@router.get("/observability/alerting/rules")
def list_observability_alert_rules():
    return deps.observability_dashboard_service.list_alert_rules()


@router.get("/observability/alerting/evaluate")
def evaluate_observability_alert_rule(
    rule_id: str = "HIGH_ERROR_RATE",
    current_value: float = 0.0,
):
    return deps.observability_dashboard_service.evaluate_alert_rule(
        rule_id=rule_id,
        current_value=current_value,
    )


@router.get("/observability/alerting/validate")
def validate_observability_alerting():
    return deps.observability_dashboard_service.validate_alerting()


@router.get("/observability/crashes/config")
def get_observability_crash_reporting_config():
    return deps.observability_dashboard_service.get_crash_reporting_config()


@router.get("/observability/crashes/recent")
def get_observability_recent_crashes(limit: int = 10):
    return deps.observability_dashboard_service.get_recent_crashes(limit=limit)


@router.get("/observability/crashes/validate")
def validate_observability_crash_reporting():
    return deps.observability_dashboard_service.validate_crash_reporting()


@router.get("/observability/sentry/config")
def get_observability_sentry_config():
    return deps.observability_dashboard_service.get_sentry_config()


@router.get("/observability/sentry/checklist")
def get_observability_sentry_checklist():
    return deps.observability_dashboard_service.get_sentry_checklist()


@router.get("/observability/sentry/validate")
def validate_observability_sentry():
    return deps.observability_dashboard_service.validate_sentry()


@router.get("/observability/runtime/snapshot")
def get_observability_runtime_snapshot():
    return deps.observability_dashboard_service.get_runtime_snapshot()


@router.get("/observability/runtime/health")
def get_observability_runtime_health():
    return deps.observability_dashboard_service.get_runtime_health()


@router.get("/observability/runtime/validate")
def validate_observability_runtime_diagnostics():
    return deps.observability_dashboard_service.validate_runtime_diagnostics()


@router.get("/observability/performance/config")
def get_observability_performance_config():
    return deps.observability_dashboard_service.get_performance_config()


@router.get("/observability/performance/evaluate")
def evaluate_observability_performance(
    p50_ms: float = 0.0,
    p95_ms: float = 0.0,
    p99_ms: float = 0.0,
    error_rate: float = 0.0,
    throughput_rps: float = 0.0,
):
    return deps.observability_dashboard_service.evaluate_performance(
        p50_ms=p50_ms,
        p95_ms=p95_ms,
        p99_ms=p99_ms,
        error_rate=error_rate,
        throughput_rps=throughput_rps,
    )


@router.get("/observability/performance/summary")
def get_observability_performance_summary():
    return deps.observability_dashboard_service.get_performance_summary()


@router.get("/observability/performance/validate")
def validate_observability_performance():
    return deps.observability_dashboard_service.validate_performance()


