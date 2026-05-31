from app.services.ai_metrics_service import AiMetricsService
from app.services.automation_metrics_service import AutomationMetricsService
from app.services.centralized_logging_service import CentralizedLoggingService
from app.services.crash_reporting_service import CrashReportingService
from app.services.distributed_tracing_service import DistributedTracingService
from app.services.grafana_dashboards_service import GrafanaDashboardsService
from app.services.metrics_collection_service import MetricsCollectionService
from app.services.observability_alerting_service import ObservabilityAlertingService
from app.services.performance_monitoring_service import PerformanceMonitoringService
from app.services.prometheus_integration_service import PrometheusIntegrationService
from app.services.runtime_diagnostics_service import RuntimeDiagnosticsService
from app.services.sentry_integration_service import SentryIntegrationService
from app.services.sla_metrics_service import SlaMetricsService


class ObservabilityDashboardService:
    def __init__(
        self,
        logging_service: CentralizedLoggingService | None = None,
        metrics_service: MetricsCollectionService | None = None,
        prometheus_service: PrometheusIntegrationService | None = None,
        grafana_service: GrafanaDashboardsService | None = None,
        ai_metrics_service: AiMetricsService | None = None,
        automation_metrics_service: AutomationMetricsService | None = None,
        sla_metrics_service: SlaMetricsService | None = None,
        tracing_service: DistributedTracingService | None = None,
        alerting_service: ObservabilityAlertingService | None = None,
        crash_reporting_service: CrashReportingService | None = None,
        sentry_service: SentryIntegrationService | None = None,
        runtime_diagnostics_service: RuntimeDiagnosticsService | None = None,
        performance_service: PerformanceMonitoringService | None = None,
    ):
        self.logging_service = logging_service or CentralizedLoggingService()
        self.metrics_service = metrics_service or MetricsCollectionService()
        self.prometheus_service = prometheus_service or PrometheusIntegrationService()
        self.grafana_service = grafana_service or GrafanaDashboardsService()
        self.ai_metrics_service = ai_metrics_service or AiMetricsService()
        self.automation_metrics_service = (
            automation_metrics_service or AutomationMetricsService()
        )
        self.sla_metrics_service = sla_metrics_service or SlaMetricsService()
        self.tracing_service = tracing_service or DistributedTracingService()
        self.alerting_service = alerting_service or ObservabilityAlertingService()
        self.crash_reporting_service = (
            crash_reporting_service or CrashReportingService()
        )
        self.sentry_service = sentry_service or SentryIntegrationService()
        self.runtime_diagnostics_service = (
            runtime_diagnostics_service or RuntimeDiagnosticsService()
        )
        self.performance_service = performance_service or PerformanceMonitoringService()

    def get_dashboard(self) -> dict:
        validations = [
            self.logging_service.validate_setup()["valid"],
            self.metrics_service.validate_setup()["valid"],
            self.prometheus_service.validate_integration()["valid"],
            self.grafana_service.validate_provisioning()["valid"],
            self.ai_metrics_service.validate_setup()["valid"],
            self.automation_metrics_service.validate_setup()["valid"],
            self.sla_metrics_service.validate_setup()["valid"],
            self.tracing_service.validate_setup()["valid"],
            self.alerting_service.validate_setup()["valid"],
            self.crash_reporting_service.validate_setup()["valid"],
            self.sentry_service.validate_setup()["valid"],
            self.runtime_diagnostics_service.validate_setup()["valid"],
            self.performance_service.validate_setup()["valid"],
        ]

        return {
            "logging": self.logging_service.get_config(),
            "metrics": self.metrics_service.get_catalog(),
            "prometheus": self.prometheus_service.validate_integration(),
            "grafana": self.grafana_service.list_dashboards(),
            "ai_metrics": self.ai_metrics_service.get_snapshot(),
            "automation_metrics": self.automation_metrics_service.get_snapshot(),
            "sla": self.sla_metrics_service.get_compliance_summary(),
            "tracing": self.tracing_service.get_config(),
            "alerting": self.alerting_service.list_rules(),
            "crash_reporting": self.crash_reporting_service.get_config(),
            "sentry": self.sentry_service.validate_setup(),
            "runtime": self.runtime_diagnostics_service.get_health_indicators(),
            "performance": self.performance_service.get_endpoint_summary(),
            "observable": all(validations),
        }

    def get_logging_config(self) -> dict:
        return self.logging_service.get_config()

    def get_log_streams(self) -> dict:
        return self.logging_service.get_log_streams()

    def search_logs(
        self,
        *,
        query: str = "",
        level: str | None = None,
        limit: int = 100,
    ) -> dict:
        return self.logging_service.search_logs(
            query=query,
            level=level,
            limit=limit,
        )

    def validate_logging(self) -> dict:
        return self.logging_service.validate_setup()

    def get_metrics_config(self) -> dict:
        return self.metrics_service.get_config()

    def get_metrics_catalog(self) -> dict:
        return self.metrics_service.get_catalog()

    def get_metrics_snapshot(
        self,
        *,
        requests_total: int = 0,
        active_connections: int = 0,
        memory_bytes: int = 0,
    ) -> dict:
        return self.metrics_service.record_snapshot(
            requests_total=requests_total,
            active_connections=active_connections,
            memory_bytes=memory_bytes,
        )

    def validate_metrics(self) -> dict:
        return self.metrics_service.validate_setup()

    def get_prometheus_config(self) -> dict:
        return self.prometheus_service.get_config()

    def validate_prometheus(self) -> dict:
        return self.prometheus_service.validate_integration()

    def get_prometheus_targets(self) -> dict:
        return self.prometheus_service.get_scrape_targets()

    def get_grafana_config(self) -> dict:
        return self.grafana_service.get_config()

    def list_grafana_dashboards(self) -> dict:
        return self.grafana_service.list_dashboards()

    def get_grafana_dashboard(self, uid: str) -> dict:
        return self.grafana_service.get_dashboard(uid)

    def validate_grafana(self) -> dict:
        return self.grafana_service.validate_provisioning()

    def get_ai_metrics_config(self) -> dict:
        return self.ai_metrics_service.get_config()

    def get_ai_metrics_catalog(self) -> dict:
        return self.ai_metrics_service.get_metrics_catalog()

    def get_ai_metrics_snapshot(
        self,
        *,
        tokens_used: int = 0,
        avg_latency_ms: float = 0.0,
        error_rate: float = 0.0,
    ) -> dict:
        return self.ai_metrics_service.get_snapshot(
            tokens_used=tokens_used,
            avg_latency_ms=avg_latency_ms,
            error_rate=error_rate,
        )

    def validate_ai_metrics(self) -> dict:
        return self.ai_metrics_service.validate_setup()

    def get_automation_metrics_config(self) -> dict:
        return self.automation_metrics_service.get_config()

    def get_automation_metrics_catalog(self) -> dict:
        return self.automation_metrics_service.get_metrics_catalog()

    def get_automation_metrics_snapshot(
        self,
        *,
        jobs_processed: int = 0,
        queue_depth: int = 0,
        success_rate: float = 100.0,
    ) -> dict:
        return self.automation_metrics_service.get_snapshot(
            jobs_processed=jobs_processed,
            queue_depth=queue_depth,
            success_rate=success_rate,
        )

    def validate_automation_metrics(self) -> dict:
        return self.automation_metrics_service.validate_setup()

    def get_sla_targets(self) -> dict:
        return self.sla_metrics_service.get_targets()

    def evaluate_sla(self, *, metric: str, actual_value: float) -> dict:
        return self.sla_metrics_service.evaluate_sla(
            metric=metric,
            actual_value=actual_value,
        )

    def get_sla_compliance(self) -> dict:
        return self.sla_metrics_service.get_compliance_summary()

    def validate_sla_metrics(self) -> dict:
        return self.sla_metrics_service.validate_setup()

    def get_tracing_config(self) -> dict:
        return self.tracing_service.get_config()

    def validate_trace_headers(self, headers: dict) -> dict:
        return self.tracing_service.validate_trace_headers(headers)

    def validate_tracing(self) -> dict:
        return self.tracing_service.validate_setup()

    def get_alerting_config(self) -> dict:
        return self.alerting_service.get_config()

    def list_alert_rules(self) -> dict:
        return self.alerting_service.list_rules()

    def evaluate_alert_rule(self, *, rule_id: str, current_value: float) -> dict:
        return self.alerting_service.evaluate_rule(
            rule_id=rule_id,
            current_value=current_value,
        )

    def validate_alerting(self) -> dict:
        return self.alerting_service.validate_setup()

    def get_crash_reporting_config(self) -> dict:
        return self.crash_reporting_service.get_config()

    def get_recent_crashes(self, *, limit: int = 10) -> dict:
        return self.crash_reporting_service.get_recent_crashes(limit=limit)

    def validate_crash_reporting(self) -> dict:
        return self.crash_reporting_service.validate_setup()

    def get_sentry_config(self) -> dict:
        return self.sentry_service.get_config()

    def get_sentry_checklist(self) -> dict:
        return self.sentry_service.get_init_checklist()

    def validate_sentry(self) -> dict:
        return self.sentry_service.validate_setup()

    def get_runtime_snapshot(self) -> dict:
        return self.runtime_diagnostics_service.get_snapshot()

    def get_runtime_health(self) -> dict:
        return self.runtime_diagnostics_service.get_health_indicators()

    def validate_runtime_diagnostics(self) -> dict:
        return self.runtime_diagnostics_service.validate_setup()

    def get_performance_config(self) -> dict:
        return self.performance_service.get_config()

    def evaluate_performance(
        self,
        *,
        p50_ms: float = 0.0,
        p95_ms: float = 0.0,
        p99_ms: float = 0.0,
        error_rate: float = 0.0,
        throughput_rps: float = 0.0,
    ) -> dict:
        return self.performance_service.evaluate_performance(
            p50_ms=p50_ms,
            p95_ms=p95_ms,
            p99_ms=p99_ms,
            error_rate=error_rate,
            throughput_rps=throughput_rps,
        )

    def get_performance_summary(self) -> dict:
        return self.performance_service.get_endpoint_summary()

    def validate_performance(self) -> dict:
        return self.performance_service.validate_setup()
