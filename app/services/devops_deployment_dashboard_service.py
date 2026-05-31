from app.services.cdn_setup_service import CdnSetupService
from app.services.centralized_logging_service import CentralizedLoggingService
from app.services.cicd_pipeline_service import CicdPipelineService
from app.services.disaster_recovery_service import DisasterRecoveryService
from app.services.docker_compose_service import DockerComposeService
from app.services.dockerization_service import DockerizationService
from app.services.environment_config_service import EnvironmentConfigService
from app.services.github_actions_service import GitHubActionsService
from app.services.horizontal_scaling_service import HorizontalScalingService
from app.services.https_setup_service import HttpsSetupService
from app.services.monitoring_stack_service import MonitoringStackService
from app.services.nginx_reverse_proxy_service import NginxReverseProxyService
from app.services.production_deployment_service import ProductionDeploymentService
from app.services.production_readiness_service import ProductionReadinessService
from app.services.production_rollout_checklist_service import (
    ProductionRolloutChecklistService,
)
from app.services.reverse_proxy_caching_service import ReverseProxyCachingService
from app.services.staging_environment_service import StagingEnvironmentService
from app.services.uptime_monitoring_service import UptimeMonitoringService
from app.services.worker_scaling_service import WorkerScalingService


class DevopsDeploymentDashboardService:
    def __init__(
        self,
        dockerization_service: DockerizationService | None = None,
        compose_service: DockerComposeService | None = None,
        environment_service: EnvironmentConfigService | None = None,
        cicd_service: CicdPipelineService | None = None,
        github_actions_service: GitHubActionsService | None = None,
        staging_service: StagingEnvironmentService | None = None,
        production_service: ProductionDeploymentService | None = None,
        nginx_service: NginxReverseProxyService | None = None,
        https_service: HttpsSetupService | None = None,
        cdn_service: CdnSetupService | None = None,
        caching_service: ReverseProxyCachingService | None = None,
        scaling_service: HorizontalScalingService | None = None,
        worker_scaling_service: WorkerScalingService | None = None,
        monitoring_service: MonitoringStackService | None = None,
        uptime_service: UptimeMonitoringService | None = None,
        logging_service: CentralizedLoggingService | None = None,
        disaster_recovery_service: DisasterRecoveryService | None = None,
        rollout_service: ProductionRolloutChecklistService | None = None,
        readiness_service: ProductionReadinessService | None = None,
    ):
        self.dockerization_service = (
            dockerization_service or DockerizationService()
        )
        self.compose_service = compose_service or DockerComposeService()
        self.environment_service = (
            environment_service or EnvironmentConfigService()
        )
        self.cicd_service = cicd_service or CicdPipelineService()
        self.github_actions_service = (
            github_actions_service or GitHubActionsService()
        )
        self.staging_service = staging_service or StagingEnvironmentService()
        self.production_service = (
            production_service or ProductionDeploymentService()
        )
        self.nginx_service = nginx_service or NginxReverseProxyService()
        self.https_service = https_service or HttpsSetupService()
        self.cdn_service = cdn_service or CdnSetupService()
        self.caching_service = caching_service or ReverseProxyCachingService()
        self.scaling_service = scaling_service or HorizontalScalingService()
        self.worker_scaling_service = (
            worker_scaling_service or WorkerScalingService()
        )
        self.monitoring_service = monitoring_service or MonitoringStackService()
        self.uptime_service = uptime_service or UptimeMonitoringService()
        self.logging_service = logging_service or CentralizedLoggingService()
        self.disaster_recovery_service = (
            disaster_recovery_service or DisasterRecoveryService()
        )
        self.rollout_service = rollout_service or ProductionRolloutChecklistService()
        self.readiness_service = readiness_service or ProductionReadinessService()

    def get_dashboard(self) -> dict:
        docker_validation = self.dockerization_service.validate_dockerfiles()
        compose_validation = self.compose_service.validate_compose_file()
        pipeline_validation = self.cicd_service.validate_pipeline()
        nginx_validation = self.nginx_service.validate_config()
        monitoring_validation = self.monitoring_service.validate_stack()

        return {
            "dockerization": self.dockerization_service.list_images(),
            "docker_compose": self.compose_service.get_stack_definition(),
            "environments": self.environment_service.list_profiles(),
            "cicd": self.cicd_service.get_pipeline_definition(),
            "github_actions": self.github_actions_service.list_workflows(),
            "staging": self.staging_service.get_config(),
            "production": self.production_service.get_config(),
            "nginx": self.nginx_service.get_config(),
            "https": self.https_service.get_tls_config(),
            "cdn": self.cdn_service.get_config(),
            "caching": self.caching_service.get_cache_config(),
            "horizontal_scaling": self.scaling_service.get_config(),
            "worker_scaling": self.worker_scaling_service.get_config(),
            "monitoring": self.monitoring_service.get_stack_definition(),
            "uptime": self.uptime_service.get_uptime_status(),
            "logging": self.logging_service.get_config(),
            "disaster_recovery": self.disaster_recovery_service.get_plan(),
            "rollout_checklist": self.rollout_service.get_checklist(),
            "healthy": (
                docker_validation["valid"]
                and compose_validation["valid"]
                and pipeline_validation["valid"]
                and nginx_validation["valid"]
                and monitoring_validation["valid"]
            ),
        }

    def get_docker_images(self) -> dict:
        return self.dockerization_service.list_images()

    def validate_dockerfiles(self) -> dict:
        return self.dockerization_service.validate_dockerfiles()

    def get_docker_build_instructions(self, image_name: str = "orgflow-api") -> dict:
        return self.dockerization_service.get_build_instructions(image_name)

    def get_compose_stack(self) -> dict:
        return self.compose_service.get_stack_definition()

    def validate_compose(self) -> dict:
        return self.compose_service.validate_compose_file()

    def get_compose_commands(self) -> dict:
        return self.compose_service.get_startup_commands()

    def get_environment_profiles(self) -> dict:
        return self.environment_service.list_profiles()

    def get_environment_profile(self, environment: str) -> dict:
        return self.environment_service.get_profile(environment)

    def validate_production_environment(self) -> dict:
        return self.environment_service.validate_production_config()

    def get_cicd_pipeline(self) -> dict:
        return self.cicd_service.get_pipeline_definition()

    def get_cicd_status(self) -> dict:
        return self.cicd_service.get_stage_status()

    def validate_cicd_pipeline(self) -> dict:
        return self.cicd_service.validate_pipeline()

    def get_github_workflows(self) -> dict:
        return self.github_actions_service.list_workflows()

    def validate_github_workflows(self) -> dict:
        return self.github_actions_service.validate_workflows()

    def get_staging_config(self) -> dict:
        return self.staging_service.get_config()

    def get_staging_status(self) -> dict:
        return self.staging_service.get_deployment_status()

    def validate_staging(self) -> dict:
        return self.staging_service.validate_readiness()

    def get_production_config(self) -> dict:
        return self.production_service.get_config()

    def get_production_status(self) -> dict:
        return self.production_service.get_deployment_status()

    def plan_production_deployment(self, version: str = "latest") -> dict:
        return self.production_service.plan_deployment(version)

    def validate_production(self) -> dict:
        return self.production_service.validate_readiness()

    def get_nginx_config(self) -> dict:
        return self.nginx_service.get_config()

    def validate_nginx(self) -> dict:
        return self.nginx_service.validate_config()

    def get_nginx_routes(self) -> dict:
        return self.nginx_service.get_routes()

    def get_https_config(self) -> dict:
        return self.https_service.get_tls_config()

    def get_https_certificate_status(self) -> dict:
        return self.https_service.get_certificate_status()

    def validate_https(self) -> dict:
        return self.https_service.validate_https_readiness()

    def get_cdn_config(self) -> dict:
        return self.cdn_service.get_config()

    def get_cdn_cache_rules(self) -> dict:
        return self.cdn_service.get_cache_rules()

    def validate_cdn(self) -> dict:
        return self.cdn_service.validate_setup()

    def get_caching_config(self) -> dict:
        return self.caching_service.get_cache_config()

    def validate_caching(self) -> dict:
        return self.caching_service.validate_config()

    def get_caching_stats(self) -> dict:
        return self.caching_service.get_cache_stats()

    def get_horizontal_scaling_config(self) -> dict:
        return self.scaling_service.get_config()

    def get_horizontal_scaling_status(self) -> dict:
        return self.scaling_service.get_scaling_status()

    def simulate_horizontal_scaling(
        self,
        *,
        cpu_percent: float = 45.0,
        memory_percent: float = 52.0,
        current_replicas: int = 3,
    ) -> dict:
        return self.scaling_service.simulate_scale_decision(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            current_replicas=current_replicas,
        )

    def get_worker_scaling_config(self) -> dict:
        return self.worker_scaling_service.get_config()

    def get_worker_scaling_status(self) -> dict:
        return self.worker_scaling_service.get_worker_status()

    def simulate_worker_scaling(
        self,
        *,
        queue_depth: int = 35,
        active_workers: int = 2,
    ) -> dict:
        return self.worker_scaling_service.simulate_scale_decision(
            queue_depth=queue_depth,
            active_workers=active_workers,
        )

    def get_monitoring_stack(self) -> dict:
        return self.monitoring_service.get_stack_definition()

    def validate_monitoring_stack(self) -> dict:
        return self.monitoring_service.validate_stack()

    def get_monitoring_metrics(self) -> dict:
        return self.monitoring_service.get_metrics_catalog()

    def get_uptime_checks(self) -> dict:
        return self.uptime_service.list_checks()

    def get_uptime_status(self) -> dict:
        return self.uptime_service.get_uptime_status()

    def get_logging_config(self) -> dict:
        return self.logging_service.get_config()

    def get_log_streams(self) -> dict:
        return self.logging_service.get_log_streams()

    def validate_logging(self) -> dict:
        return self.logging_service.validate_setup()

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

    def get_disaster_recovery_plan(self) -> dict:
        return self.disaster_recovery_service.get_plan()

    def get_disaster_recovery_rto_rpo(self) -> dict:
        return self.disaster_recovery_service.get_rto_rpo_summary()

    def run_disaster_recovery_drill(self, scenario: str = "API_OUTAGE") -> dict:
        return self.disaster_recovery_service.run_dr_drill(scenario)

    def get_rollout_checklist(self) -> dict:
        return self.rollout_service.get_checklist()

    def evaluate_rollout_checklist(
        self,
        completed_ids: list[str] | None = None,
    ) -> dict:
        return self.rollout_service.evaluate_checklist(completed_ids)

    def get_readiness_framework(self) -> dict:
        return self.readiness_service.get_review_framework()

    def run_readiness_review(
        self,
        passed_checks: list[str] | None = None,
    ) -> dict:
        return self.readiness_service.run_review(passed_checks)

    def get_readiness_blockers(
        self,
        passed_checks: list[str] | None = None,
    ) -> dict:
        return self.readiness_service.get_blockers(passed_checks)
