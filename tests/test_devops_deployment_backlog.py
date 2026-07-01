from fastapi.testclient import TestClient

import app.main as main_module
from app.auth.jwt_service import JWTService
from app.main import app
from app.services.cdn_setup_service import CdnSetupService
from app.services.centralized_logging_service import CentralizedLoggingService
from app.services.cicd_pipeline_service import CicdPipelineService
from app.services.devops_deployment_dashboard_service import (
    DevopsDeploymentDashboardService,
)
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
import app.dependencies as deps


def build_dashboard():
    return DevopsDeploymentDashboardService()


def test_dockerization_lists_and_validates_images():
    service = DockerizationService()
    images = service.list_images()

    assert images["total"] == 2
    assert images["all_present"] is True

    validation = service.validate_dockerfiles()
    assert validation["valid"] is True
    assert validation["missing"] == []

    build = service.get_build_instructions("orgflow-api")
    assert build["found"] is True
    assert "docker build" in build["build_command"]


def test_docker_compose_validates_stack():
    service = DockerComposeService()
    stack = service.get_stack_definition()

    assert "api" in stack["services"]
    assert stack["networks"] == ["orgflow-net"]

    validation = service.validate_compose_file()
    assert validation["valid"] is True
    assert validation["compose_file_exists"] is True

    commands = service.get_startup_commands()
    assert "docker compose up -d" in commands["up"]


def test_environment_config_profiles_and_production_validation():
    service = EnvironmentConfigService()
    profiles = service.list_profiles()

    assert profiles["total"] == 3
    assert all(p["env_file_exists"] for p in profiles["profiles"])

    production = service.get_profile("production")
    assert production["found"] is True
    assert production["replicas"] == 3

    validation = service.validate_production_config()
    assert validation["valid"] is True
    assert validation["missing"] == []


def test_cicd_pipeline_and_github_actions():
    cicd = CicdPipelineService()
    pipeline = cicd.get_pipeline_definition()

    assert pipeline["provider"] == "github-actions"
    assert len(pipeline["stages"]) >= 4

    validation = cicd.validate_pipeline()
    assert validation["valid"] is True

    github = GitHubActionsService()
    workflows = github.list_workflows()
    assert workflows["all_present"] is True

    workflow_validation = github.validate_workflows()
    assert workflow_validation["valid"] is True


def test_staging_and_production_environments():
    staging = StagingEnvironmentService()
    assert staging.get_config()["environment"] == "staging"
    assert staging.validate_readiness()["valid"] is True

    production = ProductionDeploymentService()
    assert production.get_config()["environment"] == "production"
    plan = production.plan_deployment("v1.2.0")
    assert plan["version"] == "v1.2.0"
    assert len(plan["steps"]) >= 6


def test_nginx_https_cdn_and_caching():
    nginx = NginxReverseProxyService()
    assert nginx.validate_config()["valid"] is True
    assert nginx.get_routes()["total"] >= 2

    https = HttpsSetupService()
    assert https.validate_https_readiness()["valid"] is True
    assert https.get_certificate_status()["valid"] is True

    cdn = CdnSetupService()
    assert cdn.validate_setup()["valid"] is True
    assert cdn.get_cache_rules()["total"] >= 2

    caching = ReverseProxyCachingService()
    assert caching.validate_config()["valid"] is True
    assert caching.get_cache_stats()["hit_rate_percent"] > 0


def test_horizontal_and_worker_scaling():
    horizontal = HorizontalScalingService()
    scale_up = horizontal.simulate_scale_decision(
        cpu_percent=85.0,
        current_replicas=3,
    )
    assert scale_up["action"] == "SCALE_UP"
    assert scale_up["target_replicas"] == 4

    workers = WorkerScalingService()
    scale_up_workers = workers.simulate_scale_decision(
        queue_depth=150,
        active_workers=2,
    )
    assert scale_up_workers["action"] == "SCALE_UP"
    assert scale_up_workers["target_workers"] == 3


def test_monitoring_uptime_and_logging():
    monitoring = MonitoringStackService()
    assert monitoring.validate_stack()["valid"] is True
    assert monitoring.get_metrics_catalog()["total"] >= 4

    uptime = UptimeMonitoringService()
    assert uptime.get_uptime_status()["overall_status"] == "UP"
    result = uptime.record_check_result(
        check_name="api_health",
        status_code=200,
        response_time_ms=45.0,
    )
    assert result["passed"] is True

    logging = CentralizedLoggingService()
    assert logging.validate_setup()["valid"] is True
    assert logging.get_log_streams()["total"] >= 3


def test_disaster_recovery_rollout_and_readiness():
    dr = DisasterRecoveryService()
    plan = dr.get_plan()
    assert plan["total_scenarios"] >= 2

    drill = dr.run_dr_drill("API_OUTAGE")
    assert drill["passed"] is True

    rollout = ProductionRolloutChecklistService()
    checklist = rollout.get_checklist()
    assert checklist["total"] >= 10

    all_ids = [item["id"] for item in checklist["items"]]
    evaluation = rollout.evaluate_checklist(all_ids)
    assert evaluation["ready"] is True
    assert evaluation["completion_percent"] == 100.0

    readiness = ProductionReadinessService()
    framework = readiness.get_review_framework()
    assert framework["total_checks"] >= 10

    all_checks = [
        check
        for category in framework["categories"]
        for check in category["checks"]
    ]
    review = readiness.run_review(all_checks)
    assert review["ready"] is True
    assert review["overall_score"] >= 80.0


def test_devops_dashboard_aggregates_all_domains():
    dashboard = build_dashboard()
    result = dashboard.get_dashboard()

    assert "dockerization" in result
    assert result["dockerization"]["all_present"] is True
    assert result["staging"]["environment"] == "staging"
    assert result["production"]["environment"] == "production"
    assert result["healthy"] is True


def _auth_headers():
    token = JWTService().issue_access_token(
        user_id="user-1",
        org_id="org-1",
        role="ADMIN",
        token_id="devops-deployment-tests",
    )
    return {"Authorization": f"Bearer {token}", "X-Organization-ID": "org-1"}


def test_devops_api_endpoints(monkeypatch):
    dashboard = build_dashboard()
    monkeypatch.setattr(
        deps,
        "devops_deployment_dashboard_service",
        dashboard,
    )

    client = TestClient(app)
    headers = _auth_headers()

    get_endpoints = [
        "/devops/dashboard",
        "/devops/docker/images",
        "/devops/docker/validate",
        "/devops/docker/build",
        "/devops/compose/stack",
        "/devops/compose/validate",
        "/devops/compose/commands",
        "/devops/environments",
        "/devops/environments/staging",
        "/devops/environments/production/validate",
        "/devops/cicd/pipeline",
        "/devops/cicd/status",
        "/devops/cicd/validate",
        "/devops/github/workflows",
        "/devops/github/validate",
        "/devops/staging/config",
        "/devops/staging/status",
        "/devops/staging/validate",
        "/devops/production/config",
        "/devops/production/status",
        "/devops/production/plan",
        "/devops/production/validate",
        "/devops/nginx/config",
        "/devops/nginx/validate",
        "/devops/nginx/routes",
        "/devops/https/config",
        "/devops/https/certificates",
        "/devops/https/validate",
        "/devops/cdn/config",
        "/devops/cdn/rules",
        "/devops/cdn/validate",
        "/devops/caching/config",
        "/devops/caching/validate",
        "/devops/caching/stats",
        "/devops/scaling/horizontal/config",
        "/devops/scaling/horizontal/status",
        "/devops/scaling/horizontal/simulate",
        "/devops/scaling/workers/config",
        "/devops/scaling/workers/status",
        "/devops/scaling/workers/simulate",
        "/devops/monitoring/stack",
        "/devops/monitoring/validate",
        "/devops/monitoring/metrics",
        "/devops/uptime/checks",
        "/devops/uptime/status",
        "/devops/logging/config",
        "/devops/logging/streams",
        "/devops/logging/validate",
        "/devops/logging/search",
        "/devops/disaster-recovery/plan",
        "/devops/disaster-recovery/rto-rpo",
        "/devops/rollout/checklist",
        "/devops/rollout/evaluate",
        "/devops/readiness/framework",
        "/devops/readiness/review",
        "/devops/readiness/blockers",
    ]

    for path in get_endpoints:
        response = client.get(path, headers=headers)
        assert response.status_code == 200, path

    post_response = client.post(
        "/devops/disaster-recovery/drill",
        headers=headers,
    )
    assert post_response.status_code == 200

    dashboard_response = client.get(
        "/devops/dashboard",
        headers=headers,
    ).json()
    assert dashboard_response["healthy"] is True
