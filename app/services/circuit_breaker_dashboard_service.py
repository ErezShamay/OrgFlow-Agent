from app.services.ai_provider_failover_service import AIProviderFailoverService
from app.services.circuit_breaker_analytics_service import (
    CircuitBreakerAnalyticsService,
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


class CircuitBreakerDashboardService:
    def __init__(
        self,
        circuit_breaker_service: CircuitBreakerService | None = None,
        threshold_service: CircuitBreakerThresholdService | None = None,
        reopen_service: CircuitBreakerReopenService | None = None,
        degradation_service: ServiceDegradationService | None = None,
        isolation_service: ProviderIsolationService | None = None,
        failover_service: AIProviderFailoverService | None = None,
        health_scoring_service: ServiceHealthScoringService | None = None,
        outage_service: OutageDetectionService | None = None,
        dependency_service: DependencyHealthMonitoringService | None = None,
        analytics_service: CircuitBreakerAnalyticsService | None = None,
    ):
        self.circuit_breaker_service = (
            circuit_breaker_service or CircuitBreakerService()
        )
        self.threshold_service = (
            threshold_service or CircuitBreakerThresholdService()
        )
        self.reopen_service = reopen_service or CircuitBreakerReopenService(
            circuit_breaker_service=self.circuit_breaker_service,
            threshold_service=self.threshold_service,
        )
        self.degradation_service = (
            degradation_service or ServiceDegradationService()
        )
        self.isolation_service = isolation_service or ProviderIsolationService()
        self.failover_service = failover_service or AIProviderFailoverService(
            isolation_service=self.isolation_service,
        )
        self.health_scoring_service = (
            health_scoring_service or ServiceHealthScoringService()
        )
        self.outage_service = outage_service or OutageDetectionService()
        self.dependency_service = (
            dependency_service or DependencyHealthMonitoringService()
        )
        self.analytics_service = (
            analytics_service or CircuitBreakerAnalyticsService()
        )

    def get_dashboard(self):
        breakers = self.circuit_breaker_service.list_breakers()
        self.isolation_service.sync_from_breakers(breakers)
        automatic_reopens = self.reopen_service.process_automatic_reopens(
            breakers
        )
        if automatic_reopens:
            breakers = self.circuit_breaker_service.list_breakers()

        return {
            "circuit_breakers": breakers,
            "breaker_count": len(breakers),
            "metrics": self.analytics_service.get_metrics(breakers),
            "analytics": self.analytics_service.get_analytics(breakers),
            "thresholds": self.threshold_service.list_thresholds(),
            "degradation": self.degradation_service.get_degradation_mode(
                breakers
            ),
            "health": self.health_scoring_service.get_overall_health_score(
                breakers
            ),
            "outages": self.outage_service.get_outage_summary(breakers),
            "dependencies": (
                self.dependency_service.get_dependency_summary(breakers)
            ),
            "ai_failover": self.failover_service.get_status(),
            "isolated_providers": (
                self.isolation_service.list_isolated_providers()
            ),
            "automatic_reopens": automatic_reopens,
        }
