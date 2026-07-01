"""DevOps & deployment routes.

Extracted from app/main.py during the 2026-07 architecture-modularization
refactor. Shared service singletons live in app/dependencies.py; shared
request models live in app/schemas/api_requests.py.
"""
from __future__ import annotations


from fastapi import APIRouter
import app.dependencies as deps


router = APIRouter()


@router.get("/devops/dashboard")
def get_devops_dashboard():
    return deps.devops_deployment_dashboard_service.get_dashboard()


@router.get("/devops/docker/images")
def list_devops_docker_images():
    return deps.devops_deployment_dashboard_service.get_docker_images()


@router.get("/devops/docker/validate")
def validate_devops_dockerfiles():
    return deps.devops_deployment_dashboard_service.validate_dockerfiles()


@router.get("/devops/docker/build")
def get_devops_docker_build_instructions(image_name: str = "orgflow-api"):
    return deps.devops_deployment_dashboard_service.get_docker_build_instructions(
        image_name,
    )


@router.get("/devops/compose/stack")
def get_devops_compose_stack():
    return deps.devops_deployment_dashboard_service.get_compose_stack()


@router.get("/devops/compose/validate")
def validate_devops_compose():
    return deps.devops_deployment_dashboard_service.validate_compose()


@router.get("/devops/compose/commands")
def get_devops_compose_commands():
    return deps.devops_deployment_dashboard_service.get_compose_commands()


@router.get("/devops/environments")
def list_devops_environment_profiles():
    return deps.devops_deployment_dashboard_service.get_environment_profiles()


@router.get("/devops/environments/{environment}")
def get_devops_environment_profile(environment: str):
    return deps.devops_deployment_dashboard_service.get_environment_profile(
        environment,
    )


@router.get("/devops/environments/production/validate")
def validate_devops_production_environment():
    return deps.devops_deployment_dashboard_service.validate_production_environment()


@router.get("/devops/cicd/pipeline")
def get_devops_cicd_pipeline():
    return deps.devops_deployment_dashboard_service.get_cicd_pipeline()


@router.get("/devops/cicd/status")
def get_devops_cicd_status():
    return deps.devops_deployment_dashboard_service.get_cicd_status()


@router.get("/devops/cicd/validate")
def validate_devops_cicd_pipeline():
    return deps.devops_deployment_dashboard_service.validate_cicd_pipeline()


@router.get("/devops/github/workflows")
def list_devops_github_workflows():
    return deps.devops_deployment_dashboard_service.get_github_workflows()


@router.get("/devops/github/validate")
def validate_devops_github_workflows():
    return deps.devops_deployment_dashboard_service.validate_github_workflows()


@router.get("/devops/staging/config")
def get_devops_staging_config():
    return deps.devops_deployment_dashboard_service.get_staging_config()


@router.get("/devops/staging/status")
def get_devops_staging_status():
    return deps.devops_deployment_dashboard_service.get_staging_status()


@router.get("/devops/staging/validate")
def validate_devops_staging():
    return deps.devops_deployment_dashboard_service.validate_staging()


@router.get("/devops/production/config")
def get_devops_production_config():
    return deps.devops_deployment_dashboard_service.get_production_config()


@router.get("/devops/production/status")
def get_devops_production_status():
    return deps.devops_deployment_dashboard_service.get_production_status()


@router.get("/devops/production/plan")
def plan_devops_production_deployment(version: str = "latest"):
    return deps.devops_deployment_dashboard_service.plan_production_deployment(
        version,
    )


@router.get("/devops/production/validate")
def validate_devops_production():
    return deps.devops_deployment_dashboard_service.validate_production()


@router.get("/devops/nginx/config")
def get_devops_nginx_config():
    return deps.devops_deployment_dashboard_service.get_nginx_config()


@router.get("/devops/nginx/validate")
def validate_devops_nginx():
    return deps.devops_deployment_dashboard_service.validate_nginx()


@router.get("/devops/nginx/routes")
def get_devops_nginx_routes():
    return deps.devops_deployment_dashboard_service.get_nginx_routes()


@router.get("/devops/https/config")
def get_devops_https_config():
    return deps.devops_deployment_dashboard_service.get_https_config()


@router.get("/devops/https/certificates")
def get_devops_https_certificate_status():
    return deps.devops_deployment_dashboard_service.get_https_certificate_status()


@router.get("/devops/https/validate")
def validate_devops_https():
    return deps.devops_deployment_dashboard_service.validate_https()


@router.get("/devops/cdn/config")
def get_devops_cdn_config():
    return deps.devops_deployment_dashboard_service.get_cdn_config()


@router.get("/devops/cdn/rules")
def get_devops_cdn_cache_rules():
    return deps.devops_deployment_dashboard_service.get_cdn_cache_rules()


@router.get("/devops/cdn/validate")
def validate_devops_cdn():
    return deps.devops_deployment_dashboard_service.validate_cdn()


@router.get("/devops/caching/config")
def get_devops_caching_config():
    return deps.devops_deployment_dashboard_service.get_caching_config()


@router.get("/devops/caching/validate")
def validate_devops_caching():
    return deps.devops_deployment_dashboard_service.validate_caching()


@router.get("/devops/caching/stats")
def get_devops_caching_stats():
    return deps.devops_deployment_dashboard_service.get_caching_stats()


@router.get("/devops/scaling/horizontal/config")
def get_devops_horizontal_scaling_config():
    return deps.devops_deployment_dashboard_service.get_horizontal_scaling_config()


@router.get("/devops/scaling/horizontal/status")
def get_devops_horizontal_scaling_status():
    return deps.devops_deployment_dashboard_service.get_horizontal_scaling_status()


@router.get("/devops/scaling/horizontal/simulate")
def simulate_devops_horizontal_scaling(
    cpu_percent: float = 45.0,
    memory_percent: float = 52.0,
    current_replicas: int = 3,
):
    return deps.devops_deployment_dashboard_service.simulate_horizontal_scaling(
        cpu_percent=cpu_percent,
        memory_percent=memory_percent,
        current_replicas=current_replicas,
    )


@router.get("/devops/scaling/workers/config")
def get_devops_worker_scaling_config():
    return deps.devops_deployment_dashboard_service.get_worker_scaling_config()


@router.get("/devops/scaling/workers/status")
def get_devops_worker_scaling_status():
    return deps.devops_deployment_dashboard_service.get_worker_scaling_status()


@router.get("/devops/scaling/workers/simulate")
def simulate_devops_worker_scaling(
    queue_depth: int = 35,
    active_workers: int = 2,
):
    return deps.devops_deployment_dashboard_service.simulate_worker_scaling(
        queue_depth=queue_depth,
        active_workers=active_workers,
    )


@router.get("/devops/monitoring/stack")
def get_devops_monitoring_stack():
    return deps.devops_deployment_dashboard_service.get_monitoring_stack()


@router.get("/devops/monitoring/validate")
def validate_devops_monitoring_stack():
    return deps.devops_deployment_dashboard_service.validate_monitoring_stack()


@router.get("/devops/monitoring/metrics")
def get_devops_monitoring_metrics():
    return deps.devops_deployment_dashboard_service.get_monitoring_metrics()


@router.get("/devops/uptime/checks")
def list_devops_uptime_checks():
    return deps.devops_deployment_dashboard_service.get_uptime_checks()


@router.get("/devops/uptime/status")
def get_devops_uptime_status():
    return deps.devops_deployment_dashboard_service.get_uptime_status()


@router.get("/devops/logging/config")
def get_devops_logging_config():
    return deps.devops_deployment_dashboard_service.get_logging_config()


@router.get("/devops/logging/streams")
def get_devops_log_streams():
    return deps.devops_deployment_dashboard_service.get_log_streams()


@router.get("/devops/logging/validate")
def validate_devops_logging():
    return deps.devops_deployment_dashboard_service.validate_logging()


@router.get("/devops/logging/search")
def search_devops_logs(
    query: str = "",
    level: str | None = None,
    limit: int = 100,
):
    return deps.devops_deployment_dashboard_service.search_logs(
        query=query,
        level=level,
        limit=limit,
    )


@router.get("/devops/disaster-recovery/plan")
def get_devops_disaster_recovery_plan():
    return deps.devops_deployment_dashboard_service.get_disaster_recovery_plan()


@router.get("/devops/disaster-recovery/rto-rpo")
def get_devops_disaster_recovery_rto_rpo():
    return deps.devops_deployment_dashboard_service.get_disaster_recovery_rto_rpo()


@router.post("/devops/disaster-recovery/drill")
def run_devops_disaster_recovery_drill(scenario: str = "API_OUTAGE"):
    return deps.devops_deployment_dashboard_service.run_disaster_recovery_drill(
        scenario,
    )


@router.get("/devops/rollout/checklist")
def get_devops_rollout_checklist():
    return deps.devops_deployment_dashboard_service.get_rollout_checklist()


@router.get("/devops/rollout/evaluate")
def evaluate_devops_rollout_checklist(
    completed_ids: str | None = None,
):
    ids = completed_ids.split(",") if completed_ids else None
    return deps.devops_deployment_dashboard_service.evaluate_rollout_checklist(ids)


@router.get("/devops/readiness/framework")
def get_devops_readiness_framework():
    return deps.devops_deployment_dashboard_service.get_readiness_framework()


@router.get("/devops/readiness/review")
def run_devops_readiness_review(passed_checks: str | None = None):
    checks = passed_checks.split(",") if passed_checks else None
    return deps.devops_deployment_dashboard_service.run_readiness_review(checks)


@router.get("/devops/readiness/blockers")
def get_devops_readiness_blockers(passed_checks: str | None = None):
    checks = passed_checks.split(",") if passed_checks else None
    return deps.devops_deployment_dashboard_service.get_readiness_blockers(checks)


