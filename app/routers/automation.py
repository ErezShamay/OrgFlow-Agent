"""Automation engine routes.

Extracted from app/main.py during the 2026-07 architecture-modularization
refactor. Shared service singletons live in app/dependencies.py; shared
request models live in app/schemas/api_requests.py.
"""
from __future__ import annotations

from app.auth import get_auth_context
from app.schemas.circuit_breaker_system import (
    CircuitBreakerReopenRequest,
    CircuitBreakerThresholdRequest,
)
from app.schemas.dead_letter_recovery import (
    DeadLetterSearchRequest,
    FailureCategorizationRequest,
    RecoveryActionRequest,
    RecoveryOrchestrationRequest,
)
from fastapi import (
    Depends,
    HTTPException,
)

from fastapi import APIRouter
import app.dependencies as deps
from app.schemas.api_requests import (
    AutomationCronScheduleRequest,
    AutomationGovernanceRequest,
    AutomationJobStatusRequest,
    AutomationQueueRequest,
    AutomationRetryEvaluationRequest,
    AutomationRetryPolicyRequest,
    AutomationSchedulerClaimRequest,
    AutomationWorkerProcessRequest,
    DynamicWorkflowBuilderRequest,
    WorkflowExecutionLogCreateRequest,
    WorkflowVersionCreateRequest,
)


router = APIRouter()


@router.get("/workflow-runs")
def get_workflow_runs():

    return deps.workflow_history.get_runs()


@router.get(
    "/automation/runs"
)
def get_automation_runs(
    auth=Depends(get_auth_context),
):

    return (
        deps.automation_monitoring_service
        .get_recent_runs(
            organization_id=auth.org_id,
        )
    )


@router.get(
    "/automation/stats"
)
def get_automation_stats(
    auth=Depends(get_auth_context),
):

    return (
        deps.automation_monitoring_service
        .get_automation_stats(
            organization_id=auth.org_id,
        )
    )


@router.get(
    "/automation/health"
)
def get_automation_health(
    auth=Depends(get_auth_context),
):

    return (
        deps.automation_monitoring_service
        .get_automation_health_dashboard(
            organization_id=auth.org_id,
        )
    )


@router.get(
    "/automation/circuit-breakers"
)
def get_automation_circuit_breakers(
    auth=Depends(get_auth_context),
):

    return (
        deps.automation_monitoring_service
        .get_circuit_breakers(
            organization_id=auth.org_id,
        )
    )


@router.get("/automation/circuit-breakers/dashboard")
def get_circuit_breaker_dashboard():
    return deps.circuit_breaker_dashboard_service.get_dashboard()


@router.get("/automation/circuit-breakers/metrics")
def get_circuit_breaker_metrics():
    breakers = deps.circuit_breaker_service.list_breakers()
    return deps.circuit_breaker_dashboard_service.analytics_service.get_metrics(
        breakers
    )


@router.get("/automation/circuit-breakers/analytics")
def get_circuit_breaker_analytics():
    breakers = deps.circuit_breaker_service.list_breakers()
    return deps.circuit_breaker_dashboard_service.analytics_service.get_analytics(
        breakers
    )


@router.get("/automation/circuit-breakers/thresholds")
def list_circuit_breaker_thresholds():
    return {
        "thresholds": deps.circuit_breaker_threshold_service.list_thresholds(),
    }


@router.post("/automation/circuit-breakers/thresholds")
def set_circuit_breaker_threshold(request: CircuitBreakerThresholdRequest):
    threshold = deps.circuit_breaker_threshold_service.set_threshold(
        breaker_key=request.breaker_key,
        failure_threshold=request.failure_threshold,
        cooldown_minutes=request.cooldown_minutes,
        half_open_success_threshold=request.half_open_success_threshold,
    )
    return {
        "breaker_key": request.breaker_key,
        "threshold": threshold,
    }


@router.post("/automation/circuit-breakers/{breaker_key}/reopen")
def reopen_circuit_breaker(
    breaker_key: str,
    request: CircuitBreakerReopenRequest,
):
    try:
        return deps.circuit_breaker_reopen_service.manual_reopen(
            breaker_key=breaker_key,
            initiated_by=request.initiated_by,
            force_closed=request.force_closed,
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/automation/circuit-breakers/degradation")
def get_service_degradation_mode():
    breakers = deps.circuit_breaker_service.list_breakers()
    return deps.circuit_breaker_dashboard_service.degradation_service.get_degradation_mode(
        breakers
    )


@router.get("/automation/circuit-breakers/health-scores")
def get_circuit_breaker_health_scores():
    breakers = deps.circuit_breaker_service.list_breakers()
    return deps.circuit_breaker_dashboard_service.health_scoring_service.get_overall_health_score(
        breakers
    )


@router.get("/automation/circuit-breakers/outages")
def get_circuit_breaker_outages():
    breakers = deps.circuit_breaker_service.list_breakers()
    return deps.circuit_breaker_dashboard_service.outage_service.get_outage_summary(
        breakers
    )


@router.get("/automation/circuit-breakers/dependencies")
def get_circuit_breaker_dependencies():
    breakers = deps.circuit_breaker_service.list_breakers()
    return deps.circuit_breaker_dashboard_service.dependency_service.get_dependency_summary(
        breakers
    )


@router.get("/automation/circuit-breakers/ai-failover")
def get_ai_provider_failover_status():
    return deps.circuit_breaker_dashboard_service.failover_service.get_status()


@router.get(
    "/automation/ai-recovery"
)
def get_automation_ai_recovery(
    auth=Depends(get_auth_context),
):

    return (
        deps.automation_monitoring_service
        .get_ai_recovery_monitoring(
            organization_id=auth.org_id,
        )
    )


@router.get("/automation/dead-letters/dashboard")
def get_dead_letter_recovery_dashboard(
    auth=Depends(get_auth_context),
):
    return deps.recovery_dashboard_service.get_dashboard(
        organization_id=auth.org_id,
    )


@router.get("/automation/dead-letters")
def search_dead_letters(
    execution_type: str | None = None,
    failure_type: str | None = None,
    severity: str | None = None,
    project_id: str | None = None,
    query: str | None = None,
    limit: int = 50,
    auth=Depends(get_auth_context),
):
    return {
        "dead_letters": deps.dead_letter_recovery_service.search_dead_letters(
            execution_type=execution_type,
            failure_type=failure_type,
            severity=severity,
            project_id=project_id,
            query=query,
            limit=limit,
            organization_id=auth.org_id,
        ),
    }


@router.get("/automation/dead-letters/metrics")
def get_dead_letter_recovery_metrics(
    auth=Depends(get_auth_context),
):
    return deps.dead_letter_recovery_service.get_metrics(
        organization_id=auth.org_id,
    )


@router.get("/automation/dead-letters/analytics")
def get_dead_letter_analytics(
    auth=Depends(get_auth_context),
):
    return deps.dead_letter_recovery_service.get_analytics(
        organization_id=auth.org_id,
    )


@router.get("/automation/dead-letters/audit-logs")
def get_recovery_audit_logs(
    execution_log_id: str | None = None,
    limit: int = 100,
):
    return {
        "entries": deps.dead_letter_recovery_service.list_audit_logs(
            execution_log_id=execution_log_id,
            limit=limit,
        ),
    }


@router.get("/automation/dead-letters/replay-tracking")
def get_recovery_replay_tracking(
    execution_log_id: str | None = None,
    limit: int = 100,
):
    return {
        "replays": deps.dead_letter_recovery_service.list_replay_tracking(
            execution_log_id=execution_log_id,
            limit=limit,
        ),
    }


@router.get("/automation/dead-letters/auto-recovery-rules")
def list_auto_recovery_rules():
    return {
        "rules": deps.auto_recovery_rules_service.list_rules(),
    }


@router.post("/automation/dead-letters/search")
def post_search_dead_letters(
    request: DeadLetterSearchRequest,
    auth=Depends(get_auth_context),
):
    return {
        "dead_letters": deps.dead_letter_recovery_service.search_dead_letters(
            execution_type=request.execution_type,
            failure_type=request.failure_type,
            severity=request.severity,
            project_id=request.project_id,
            query=request.query,
            limit=request.limit,
            organization_id=auth.org_id,
        ),
    }


@router.post("/automation/dead-letters/{log_id}/replay")
def replay_dead_letter_execution(
    log_id: str,
    request: RecoveryActionRequest,
    auth=Depends(get_auth_context),
):
    try:
        return deps.dead_letter_recovery_service.replay_execution(
            log_id=log_id,
            initiated_by=request.initiated_by,
            organization_id=auth.org_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/automation/dead-letters/{log_id}/retry")
def retry_dead_letter_execution(
    log_id: str,
    request: RecoveryActionRequest,
    auth=Depends(get_auth_context),
):
    try:
        return deps.dead_letter_recovery_service.retry_dead_letter(
            log_id=log_id,
            initiated_by=request.initiated_by,
            organization_id=auth.org_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/automation/dead-letters/{log_id}/manual-recover")
def manual_recover_dead_letter(
    log_id: str,
    request: RecoveryActionRequest,
    auth=Depends(get_auth_context),
):
    try:
        return deps.dead_letter_recovery_service.manual_recover(
            log_id=log_id,
            initiated_by=request.initiated_by,
            organization_id=auth.org_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/automation/dead-letters/categorize-failure")
def categorize_dead_letter_failure(request: FailureCategorizationRequest):
    return deps.dead_letter_recovery_service.categorize_failure(
        error_message=request.error_message,
    )


@router.post("/automation/dead-letters/orchestrate")
def orchestrate_dead_letter_recovery(request: RecoveryOrchestrationRequest):
    return deps.recovery_orchestration_service.orchestrate_recovery_cycle(
        initiated_by=request.initiated_by,
        limit=request.limit,
    )


@router.get(
    "/automation/ai-execution-logs"
)
def get_automation_ai_execution_logs(
    auth=Depends(get_auth_context),
):

    return (
        deps.automation_monitoring_service
        .get_ai_execution_logs_dashboard(
            organization_id=auth.org_id,
        )
    )


@router.get(
    "/automation/schedules"
)
def get_automation_schedules():
    return {
        "jobs":
            deps.automation_cron_management_service
            .list_job_schedules()
    }


@router.put(
    "/automation/schedules/{job_id}"
)
def update_automation_schedule(
    job_id: str,
    request: AutomationCronScheduleRequest,
):
    try:
        return (
            deps.automation_cron_management_service
            .set_job_cron(
                job_id=job_id,
                cron_expression=request.cron,
                enabled=request.enabled,
            )
        )
    except (KeyError, LookupError) as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


@router.patch(
    "/automation/schedules/{job_id}/status"
)
def set_automation_schedule_status(
    job_id: str,
    request: AutomationJobStatusRequest,
):
    try:
        return (
            deps.automation_cron_management_service
            .set_job_enabled(
                job_id=job_id,
                enabled=request.enabled,
            )
        )
    except (KeyError, LookupError) as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc


@router.post(
    "/automation/runs/{run_id}/replay"
)
def replay_automation_run(
    run_id: str,
):
    try:
        return (
            deps.automation_replay_service
            .replay_run(run_id)
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


@router.get(
    "/automation/control/status"
)
def get_automation_control_status():
    return (
        deps.automation_control_service
        .get_status()
    )


@router.post(
    "/automation/control/pause"
)
def pause_automation_scheduler():
    return (
        deps.automation_control_service
        .pause()
    )


@router.post(
    "/automation/control/resume"
)
def resume_automation_scheduler():
    return (
        deps.automation_control_service
        .resume()
    )


@router.get("/automation/queue")
def list_automation_queue(status: str | None = None):
    return {
        "items": deps.automation_job_queue_service.list_items(status=status),
    }


@router.post("/automation/queue")
def enqueue_automation_job(request: AutomationQueueRequest):
    return deps.automation_job_queue_service.enqueue(
        job_name=request.job_name,
        payload=request.payload,
        priority=request.priority,
        idempotency_key=request.idempotency_key,
    )


@router.get("/automation/workers/stats")
def get_automation_worker_stats():
    return deps.automation_worker_service.get_worker_stats()


@router.post("/automation/workers/process-next")
def process_next_automation_queue_item(request: AutomationWorkerProcessRequest):
    handlers = {
        "sla_monitoring": lambda payload: {
            "handled": True,
            "job_name": "sla_monitoring",
            "payload": payload,
        },
        "ai_automation": lambda payload: {
            "handled": True,
            "job_name": "ai_automation",
            "payload": payload,
        },
        "ai_recovery": lambda payload: {
            "handled": True,
            "job_name": "ai_recovery",
            "payload": payload,
        },
    }
    return deps.automation_worker_service.process_next(
        worker_id=request.worker_id,
        handlers=handlers,
    )


@router.get("/automation/retry-policies/{job_name}")
def get_automation_retry_policy(job_name: str):
    return deps.automation_retry_policy_service.get_policy(job_name)


@router.put("/automation/retry-policies/{job_name}")
def set_automation_retry_policy(job_name: str, request: AutomationRetryPolicyRequest):
    return deps.automation_retry_policy_service.set_policy(
        job_name=job_name,
        max_attempts=request.max_attempts,
        backoff_seconds=request.backoff_seconds,
        multiplier=request.multiplier,
    )


@router.post("/automation/retry-policies/{job_name}/evaluate")
def evaluate_automation_retry_policy(job_name: str, request: AutomationRetryEvaluationRequest):
    return deps.automation_retry_policy_service.evaluate_retry(
        job_name=job_name,
        attempts=request.attempts,
    )


@router.post("/automation/scheduler/claim-tick")
def claim_automation_scheduler_tick(request: AutomationSchedulerClaimRequest):
    return deps.automation_scheduler_guard_service.claim_tick(
        job_name=request.job_name,
        owner_id=request.owner_id,
        window_seconds=request.window_seconds,
    )


@router.post("/automation/governance/evaluate")
def evaluate_automation_governance(request: AutomationGovernanceRequest):
    return deps.automation_governance_service.evaluate(
        job_name=request.job_name,
        payload=request.payload,
        actor=request.actor,
    )


@router.post("/automation/workflows/versions")
def create_workflow_version(request: WorkflowVersionCreateRequest):
    return deps.workflow_versioning_service.create_version(
        workflow_name=request.workflow_name,
        definition=request.definition,
        published_by=request.published_by,
        activate=request.activate,
    )


@router.get("/automation/workflows/{workflow_name}/versions")
def list_workflow_versions(workflow_name: str):
    return {
        "workflow_name": workflow_name,
        "versions": deps.workflow_versioning_service.list_versions(workflow_name),
    }


@router.get("/automation/workflows/{workflow_name}/active-version")
def get_active_workflow_version(workflow_name: str):
    active = deps.workflow_versioning_service.get_active_version(workflow_name)
    if not active:
        raise HTTPException(status_code=404, detail="Workflow version not found")
    return active


@router.post("/automation/runs/{run_id}/logs")
def append_workflow_execution_log(run_id: str, request: WorkflowExecutionLogCreateRequest):
    return deps.workflow_execution_log_service.append_log(
        run_id=run_id,
        level=request.level,
        message=request.message,
        context=request.context,
    )


@router.get("/automation/runs/{run_id}/logs")
def list_workflow_execution_logs(run_id: str, limit: int = 200):
    return {
        "run_id": run_id,
        "entries": deps.workflow_execution_log_service.list_logs(
            run_id=run_id,
            limit=limit,
        ),
    }


@router.post("/automation/workflows/builder")
def build_dynamic_workflow(request: DynamicWorkflowBuilderRequest):
    try:
        return deps.dynamic_automation_builder_service.build_workflow(
            workflow_name=request.workflow_name,
            steps=request.steps,
            created_by=request.created_by,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


