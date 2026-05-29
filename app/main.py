import shutil

from datetime import UTC, datetime
from pathlib import Path

from fastapi import (
    FastAPI,
    HTTPException,
    Depends,
    Request,
    WebSocket,
    WebSocketDisconnect,
    UploadFile,
    File,
    Form,
)
from fastapi.responses import JSONResponse

from fastapi.middleware.cors import (
    CORSMiddleware
)

from pydantic import BaseModel, Field

from app.config.settings import settings
from app.config import config_manager
from app.auth import (
    APIAuthorizationMiddleware,
    JWTService,
    PERMISSION_MATRIX,
    get_auth_context,
    require_permission,
)

from app.agent.orchestrator import (
    Orchestrator
)

from app.agent.workflow_history import (
    WorkflowHistory
)

from app.services.approval_service import (
    ApprovalService
)

from app.services.ai_review_service import (
    AIReviewService
)

from app.services.operational_action_service import (
    OperationalActionService
)

from app.services.project_insights_service import (
    ProjectInsightsService,
)

from app.services.project_service import (
    ProjectService,
)

from app.repositories.project_repository import (
    ProjectRepository
)

from app.repositories.organization_repository import (
    OrganizationRepository
)

from app.repositories.ai_interpretation_repository import (
    AIInterpretationRepository
)

from app.repositories.operational_action_repository import (
    OperationalActionRepository
)

from app.repositories.weekly_report_repository import (
    WeeklyReportRepository
)

from app.repositories.workspace_activity_repository import (
    WorkspaceActivityRepository,
)

from app.services.report_processing_service import (
    ReportProcessingService,
)

from app.services.operational_action_service import (
    OperationalActionService,
)

from app.services.project_workspace_service import (
    ProjectWorkspaceService
)

from app.services.workspace_activity_service import (
    WorkspaceActivityService
)

from app.services.operational_summary_service import (
    OperationalSummaryService
)

from app.services.profile_service import (
    ProfileService
)

from app.services.notification_service import (
    NotificationService
)

from app.services.portfolio_insights_service import (
    PortfolioInsightsService
)

from app.services.alert_engine_service import (
    AlertEngineService
)

from app.services.automation_monitoring_service import (
    AutomationMonitoringService
)
from app.services.automation_cron_management_service import (
    AutomationCronManagementService
)
from app.services.automation_replay_service import (
    AutomationReplayService
)
from app.services.automation_control_service import (
    AutomationControlService
)
from app.services.automation_job_queue_service import (
    AutomationJobQueueService
)
from app.services.automation_retry_policy_service import (
    AutomationRetryPolicyService
)
from app.services.automation_worker_service import (
    AutomationWorkerService
)
from app.services.automation_scheduler_guard_service import (
    AutomationSchedulerGuardService
)
from app.services.automation_governance_service import (
    AutomationGovernanceService
)
from app.services.workflow_versioning_service import (
    WorkflowVersioningService
)
from app.services.workflow_execution_log_service import (
    WorkflowExecutionLogService
)
from app.services.dynamic_automation_builder_service import (
    DynamicAutomationBuilderService
)
from app.services.dead_letter_recovery_service import (
    DeadLetterRecoveryService,
)
from app.services.recovery_dashboard_service import (
    RecoveryDashboardService,
)
from app.services.recovery_orchestration_service import (
    RecoveryOrchestrationService,
)
from app.services.auto_recovery_rules_service import (
    AutoRecoveryRulesService,
)
from app.schemas.dead_letter_recovery import (
    DeadLetterSearchRequest,
    RecoveryActionRequest,
    FailureCategorizationRequest,
    RecoveryOrchestrationRequest,
)
from app.services.circuit_breaker_dashboard_service import (
    CircuitBreakerDashboardService,
)
from app.services.circuit_breaker_threshold_service import (
    CircuitBreakerThresholdService,
)
from app.services.circuit_breaker_reopen_service import (
    CircuitBreakerReopenService,
)
from app.services.circuit_breaker_service import (
    CircuitBreakerService,
)
from app.schemas.circuit_breaker_system import (
    CircuitBreakerThresholdRequest,
    CircuitBreakerReopenRequest,
)

# ==========================================
# EXCEPTION HANDLING & LOGGING
# ==========================================

from app.exceptions import (
    GlobalExceptionHandler,
    IdempotencyMiddleware,
    RequestLoggingMiddleware,
    setup_logging,
    get_logger,
)

# ==========================================
# AUTOMATION
# ==========================================

from app.automation.scheduler import (
    scheduler
)

from app.automation.jobs import (
    register_automation_jobs
)

automation_monitoring_service = (
    AutomationMonitoringService()
)
automation_cron_management_service = (
    AutomationCronManagementService()
)
automation_replay_service = (
    AutomationReplayService()
)
automation_control_service = (
    AutomationControlService()
)
automation_job_queue_service = (
    AutomationJobQueueService()
)
automation_retry_policy_service = (
    AutomationRetryPolicyService()
)
automation_worker_service = (
    AutomationWorkerService(
        queue_service=automation_job_queue_service,
        retry_policy_service=automation_retry_policy_service,
    )
)
automation_worker_service.register_worker(
    "worker-default",
    capabilities=["sla_monitoring", "ai_automation", "ai_recovery"],
)
automation_scheduler_guard_service = (
    AutomationSchedulerGuardService()
)
automation_governance_service = (
    AutomationGovernanceService()
)
workflow_versioning_service = (
    WorkflowVersioningService()
)
workflow_execution_log_service = (
    WorkflowExecutionLogService()
)
dynamic_automation_builder_service = (
    DynamicAutomationBuilderService()
)
dead_letter_recovery_service = (
    DeadLetterRecoveryService()
)
recovery_dashboard_service = (
    RecoveryDashboardService(
        dead_letter_recovery_service=dead_letter_recovery_service,
    )
)
recovery_orchestration_service = (
    RecoveryOrchestrationService(
        dead_letter_recovery_service=dead_letter_recovery_service,
    )
)
auto_recovery_rules_service = (
    AutoRecoveryRulesService()
)
circuit_breaker_service = (
    CircuitBreakerService()
)
circuit_breaker_threshold_service = (
    CircuitBreakerThresholdService()
)
circuit_breaker_reopen_service = (
    CircuitBreakerReopenService(
        circuit_breaker_service=circuit_breaker_service,
        threshold_service=circuit_breaker_threshold_service,
    )
)
circuit_breaker_dashboard_service = (
    CircuitBreakerDashboardService(
        circuit_breaker_service=circuit_breaker_service,
        threshold_service=circuit_breaker_threshold_service,
        reopen_service=circuit_breaker_reopen_service,
    )
)

# ==========================================
# LOGGING SETUP
# ==========================================

setup_logging()
logger = get_logger(__name__)

logger.info("OrgFlow Agent starting up")
jwt_service = JWTService()

FRONTEND_URL = str(settings.FRONTEND_URL)
IS_AUTOMATION_ENABLED = settings.FEATURE_FLAGS.enable_automation

FRONTEND_URLS = [
    FRONTEND_URL,
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://localhost:3000",
    "https://127.0.0.1:3000",
]

# ==========================================
# APP
# ==========================================

app = FastAPI()
app.state.startup_complete = False

DEMO_ORGANIZATION_ID = (
    "bb2c760b-81cb-4e49-b057-4426406d5e71"
)


class WorkspaceConnectionManager:
    def __init__(self):
        self._project_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, project_id: str, websocket: WebSocket):
        await websocket.accept()
        self._project_connections.setdefault(project_id, []).append(websocket)

    def disconnect(self, project_id: str, websocket: WebSocket):
        sockets = self._project_connections.get(project_id, [])
        self._project_connections[project_id] = [
            candidate for candidate in sockets if candidate is not websocket
        ]

    async def broadcast_activity(self, project_id: str, activity: dict):
        sockets = list(self._project_connections.get(project_id, []))
        disconnected: list[WebSocket] = []
        for websocket in sockets:
            try:
                await websocket.send_json(
                    {
                        "event": "workspace.activity.created",
                        "project_id": project_id,
                        "activity": activity,
                    }
                )
            except RuntimeError:
                disconnected.append(websocket)
        for websocket in disconnected:
            self.disconnect(project_id, websocket)


class NotificationConnectionManager:
    def __init__(self):
        self._profile_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, profile_id: str, websocket: WebSocket):
        await websocket.accept()
        self._profile_connections.setdefault(profile_id, []).append(websocket)

    def disconnect(self, profile_id: str, websocket: WebSocket):
        sockets = self._profile_connections.get(profile_id, [])
        self._profile_connections[profile_id] = [
            candidate for candidate in sockets if candidate is not websocket
        ]

    async def broadcast_notification(self, profile_id: str, notification: dict):
        sockets = list(self._profile_connections.get(profile_id, []))
        disconnected: list[WebSocket] = []
        for websocket in sockets:
            try:
                await websocket.send_json(
                    {
                        "event": "notification.created",
                        "profile_id": profile_id,
                        "notification": notification,
                    }
                )
            except RuntimeError:
                disconnected.append(websocket)
        for websocket in disconnected:
            self.disconnect(profile_id, websocket)

# ==========================================
# MIDDLEWARE
# ==========================================

# Add request logging middleware before exception handling
app.add_middleware(
    RequestLoggingMiddleware
)

# Add idempotency middleware for write requests
app.add_middleware(
    IdempotencyMiddleware
)

# Add global exception handler middleware (must be first)
app.add_middleware(
    GlobalExceptionHandler
)

app.add_middleware(
    APIAuthorizationMiddleware,
    public_paths={
        "/",
        "/healthcheck",
        "/readiness",
        "/liveness",
        "/__test/error",
        "/feature-flags",
        "/config",
        "/config/reload",
        "/secrets/rotation-status",
        "/auth/refresh",
    },
)

# ==========================================
# CORS
# ==========================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=FRONTEND_URLS,

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)

# ==========================================
# SERVICES
# ==========================================

orchestrator = (
    Orchestrator()
)

workflow_history = (
    WorkflowHistory()
)

approval_service = (
    ApprovalService()
)

ai_review_service = (
    AIReviewService()
)

operational_action_service = (
    OperationalActionService()
)

project_service = (
    ProjectService()
)

project_repository = (
    ProjectRepository()
)

organization_repository = (
    OrganizationRepository()
)

ai_interpretation_repository = (
    AIInterpretationRepository()
)

operational_action_repository = (
    OperationalActionRepository()
)

weekly_report_repository = (
    WeeklyReportRepository()
)

project_workspace_service = (
    ProjectWorkspaceService()
)

operational_summary_service = (
    OperationalSummaryService()
)

portfolio_insights_service = (
    PortfolioInsightsService()
)

alert_engine_service = (
    AlertEngineService()
)

profile_service = (
    ProfileService()
)

notification_service = (
    NotificationService()
)

report_processing_service = (
    ReportProcessingService()
)
workspace_activity_service = (
    WorkspaceActivityService()
)
workspace_connection_manager = (
    WorkspaceConnectionManager()
)
notification_connection_manager = (
    NotificationConnectionManager()
)

# ==========================================
# AUTOMATION ENGINE
# ==========================================

@app.on_event("startup")
def startup_event():
    if IS_AUTOMATION_ENABLED:
        register_automation_jobs()

        if not scheduler.running:
            scheduler.start()
            print(
                "[AUTOMATION] Scheduler started"
            )
    else:
        logger.info(
            "Automation disabled by feature flag"
        )

    app.state.startup_complete = True


@app.on_event("shutdown")
def shutdown_event():
    app.state.startup_complete = False

    if scheduler.running:
        scheduler.shutdown(wait=False)
        print(
            "[AUTOMATION] Scheduler stopped"
        )

# ==========================================
# REQUEST MODELS
# ==========================================

class AgentRequest(
    BaseModel
):

    user_request: str


class ReviewDecisionRequest(
    BaseModel
):

    reviewed_by: str

    review_notes: str | None = None


class AssignActionRequest(
    BaseModel
):

    assigned_to: str


class AssignReviewerRequest(
    BaseModel
):

    reviewer_id: str


class HumanOverrideRequest(
    BaseModel
):

    overridden_by: str
    override_reason: str


class RecommendationReviewRequest(
    BaseModel
):

    reviewed_by: str
    decision: str
    review_notes: str | None = None


class ReviewCommentRequest(
    BaseModel
):
    author: str
    comment: str


class ReviewNotificationRequest(
    BaseModel
):
    recipient_id: str
    message: str
    channel: str = "IN_APP"


class ManualApprovalRequest(
    BaseModel
):
    requested_by: str
    notes: str | None = None


class CreateProjectRequest(
    BaseModel
):
    project_name: str
    supervisor_name: str
    supervisor_email: str | None = None
    organization_id: str | None = None
    owner_id: str | None = None
    tags: list[str] = Field(default_factory=list)


class EditProjectRequest(
    BaseModel
):
    project_name: str | None = None
    supervisor_name: str | None = None
    supervisor_email: str | None = None


class ProjectTagsRequest(
    BaseModel
):
    tags: list[str]


class ProjectOwnerRequest(
    BaseModel
):
    owner_id: str


class ProjectLifecycleRequest(
    BaseModel
):
    lifecycle_phase: str


class ProjectAttachmentRequest(
    BaseModel
):
    filename: str
    uploaded_by: str


class ProjectCommentRequest(
    BaseModel
):
    comment: str
    author: str


class ReportAttachmentRequest(
    BaseModel
):
    report_id: str
    filename: str
    uploaded_by: str


class ReportTagsRequest(
    BaseModel
):
    tags: list[str]


class ActionRecurringRequest(
    BaseModel
):
    title: str
    recurrence_rule: str
    created_by: str


class ActionBulkRequest(
    BaseModel
):
    actions: list[dict]


class ActionAttachmentRequest(
    BaseModel
):
    filename: str
    uploaded_by: str


class ActionNotificationRequest(
    BaseModel
):
    recipient_id: str
    message: str
    channel: str = "IN_APP"


class NotificationCreateRequest(
    BaseModel
):
    title: str
    message: str
    notification_type: str = "GENERAL"
    channel: str = "IN_APP"
    channels: list[str] | None = None
    category: str | None = None
    priority: str = "NORMAL"
    banner: bool = False
    max_attempts: int = 3
    force_fail_channels: list[str] = Field(default_factory=list)


class NotificationReadSyncRequest(
    BaseModel
):
    read_ids: list[str]


class NotificationPreferenceRequest(
    BaseModel
):
    channels: dict[str, bool] = Field(default_factory=dict)
    categories: dict[str, bool] = Field(default_factory=dict)


class NotificationEscalationRequest(
    BaseModel
):
    title: str
    message: str
    escalation_level: str


class ActionCommentRequest(
    BaseModel
):
    comment: str
    created_by: str


class ActionRetryRequest(
    BaseModel
):
    reason: str


class ActionOwnerRequest(
    BaseModel
):
    owner_id: str


class ActionEscalationRequest(
    BaseModel
):
    level: str
    reason: str


class ActionAIGenerationRequest(
    BaseModel
):
    context: str


class ActionTemplateRequest(
    BaseModel
):
    name: str
    title: str
    description: str
    category: str


class ActionTemplateApplyRequest(
    BaseModel
):
    created_by: str


class ActionCategoryRequest(
    BaseModel
):
    category: str


class WorkspaceActivityCreateRequest(
    BaseModel
):
    activity_type: str
    title: str
    description: str | None = None
    metadata: dict = Field(default_factory=dict)
    actor_id: str | None = None


class WorkspaceLayoutRequest(
    BaseModel
):
    layout: dict


class WorkspaceWidgetsRequest(
    BaseModel
):
    widgets: list[dict]


class CrossProjectWorkspaceRequest(
    BaseModel
):
    project_ids: list[str]
    limit: int = 50


class AutomationCronScheduleRequest(
    BaseModel
):
    cron: str
    enabled: bool = True


class AutomationJobStatusRequest(
    BaseModel
):
    enabled: bool


class AutomationQueueRequest(
    BaseModel
):
    job_name: str
    payload: dict = Field(default_factory=dict)
    priority: int = 5
    idempotency_key: str | None = None


class AutomationWorkerProcessRequest(
    BaseModel
):
    worker_id: str = "worker-default"


class AutomationRetryPolicyRequest(
    BaseModel
):
    max_attempts: int
    backoff_seconds: int
    multiplier: int = 2


class AutomationRetryEvaluationRequest(
    BaseModel
):
    attempts: int


class AutomationSchedulerClaimRequest(
    BaseModel
):
    job_name: str
    owner_id: str = "scheduler"
    window_seconds: int = 30


class AutomationGovernanceRequest(
    BaseModel
):
    job_name: str
    payload: dict = Field(default_factory=dict)
    actor: str = "system"


class WorkflowVersionCreateRequest(
    BaseModel
):
    workflow_name: str
    definition: dict = Field(default_factory=dict)
    published_by: str
    activate: bool = True


class WorkflowExecutionLogCreateRequest(
    BaseModel
):
    level: str
    message: str
    context: dict = Field(default_factory=dict)


class DynamicWorkflowBuilderRequest(
    BaseModel
):
    workflow_name: str
    created_by: str
    steps: list[dict]


# ==========================================
# ROOT
# ==========================================

@app.get("/")
def root():

    return {
        "message":
            "OrgFlow AI Agent is running"
    }


@app.get("/healthcheck")
def healthcheck():

    return {
        "status": "ok",
        "service": "orgflow-agent",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/readiness")
def readiness():
    checks = {
        "startup_complete": bool(app.state.startup_complete),
        "scheduler_running": bool(scheduler.running) if IS_AUTOMATION_ENABLED else True,
        "automation_enabled": IS_AUTOMATION_ENABLED,
        "supabase_configured": bool(
            settings.SUPABASE_URL and settings.SUPABASE_KEY
        ),
    }

    is_ready = checks["startup_complete"] and checks["scheduler_running"]
    payload = {
        "status": "ready" if is_ready else "not_ready",
        "service": "orgflow-agent",
        "checks": checks,
    }

    if not is_ready:
        return JSONResponse(status_code=503, content=payload)

    return payload


@app.get("/liveness")
def liveness():
    return {
        "status": "alive",
        "service": "orgflow-agent",
        "environment": settings.ENVIRONMENT,
        "timestamp": (
            datetime
            .now(UTC)
            .isoformat()
        ),
    }


@app.get("/feature-flags")
def get_feature_flags():
    current_settings = config_manager.get_settings()
    return {
        "environment": current_settings.ENVIRONMENT,
        "flags": current_settings.FEATURE_FLAGS.model_dump(),
    }


@app.get("/config")
def get_runtime_config():
    return {
        "environment": config_manager.get_settings().ENVIRONMENT,
        "config": config_manager.get_safe_snapshot(),
    }


@app.post("/config/reload")
def reload_runtime_config():
    updated = config_manager.force_reload()
    return {
        "status": "reloaded",
        "environment": updated.ENVIRONMENT,
    }


@app.get("/secrets/rotation-status")
def get_secret_rotation_status():
    return config_manager.get_secret_rotation_status()


@app.get("/auth/me")
def get_current_session(auth=Depends(get_auth_context)):
    return {
        "user_id": auth.user_id,
        "org_id": auth.org_id,
        "role": auth.role,
        "effective_user_id": auth.effective_user_id,
        "permissions": sorted(auth.permissions),
    }


@app.get("/auth/permission-matrix")
def get_permission_matrix():
    return {role: sorted(perms) for role, perms in PERMISSION_MATRIX.items()}


@app.get("/auth/tenant/check")
def tenant_check(auth=Depends(get_auth_context)):
    return {"status": "ok", "org_id": auth.org_id}


@app.get("/auth/secure/reports")
def secure_reports(_: object = Depends(require_permission("reports:read"))):
    return {"status": "ok"}


@app.get("/auth/secure/admin")
def secure_admin(_: object = Depends(require_permission("users:write"))):
    return {"status": "ok"}


@app.get("/auth/impersonation/status")
def impersonation_status(auth=Depends(get_auth_context)):
    return {
        "is_impersonating": bool(auth.effective_user_id),
        "actor_user_id": auth.user_id,
        "effective_user_id": auth.actor_user_id,
    }


@app.post("/auth/refresh")
def refresh_access_token(request: Request):
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer refresh token")

    refresh_token = auth_header.replace("Bearer ", "", 1).strip()
    payload = jwt_service.decode_refresh_token(refresh_token)
    access_token = jwt_service.issue_access_token(
        user_id=payload["sub"],
        org_id=payload["org_id"],
        role=payload["role"],
        token_id=str(payload.get("jti", "refresh-rotation")),
    )
    logger.info(
        "Refresh token exchanged",
        extra={
            "event": "audit.refresh",
            "user_id": payload["sub"],
            "org_id": payload["org_id"],
        },
    )
    return {"access_token": access_token, "token_type": "Bearer"}

# ==========================================
# AGENT APIs
# ==========================================

@app.post("/agent/run")
def run_agent(
    request: AgentRequest
):

    return orchestrator.run(
        request.user_request
    )


@app.get("/workflow-runs")
def get_workflow_runs():

    return workflow_history.get_runs()

# ==========================================
# APPROVAL APIs
# ==========================================

@app.post(
    "/approval/{approval_id}/approve"
)
def approve_request(
    approval_id: int
):

    return approval_service.approve(
        approval_id
    )


@app.get(
    "/approval/{approval_id}"
)
def get_approval_request(
    approval_id: int
):

    return approval_service.get_request(
        approval_id
    )

# ==========================================
# AI REVIEW APIs
# ==========================================

@app.get("/reviews/pending")
def get_pending_reviews():

    return (
        ai_review_service
        .get_pending_reviews()
    )


@app.get("/reviews/dashboard")
def get_review_dashboard(limit: int = 20):

    return (
        ai_review_service
        .get_review_dashboard(
            recent_limit=limit
        )
    )


@app.post("/reviews/{interpretation_id}/assign")
def assign_review_reviewer(
    interpretation_id: str,
    request: AssignReviewerRequest,
):
    assignment = (
        ai_review_service
        .assign_reviewer(
            interpretation_id=
                interpretation_id,
            reviewer_id=
                request.reviewer_id,
        )
    )

    if not assignment:
        raise HTTPException(
            status_code=404,
            detail="Review not found"
        )

    return assignment


@app.get("/reviews/sla")
def get_reviews_sla_tracking(target_hours: int = 48):
    return (
        ai_review_service
        .get_review_sla_tracking(
            target_hours=target_hours
        )
    )


@app.get("/reviews/{interpretation_id}/confidence")
def get_review_confidence(
    interpretation_id: str,
):
    confidence_payload = (
        ai_review_service
        .get_review_confidence(
            interpretation_id
        )
    )

    if not confidence_payload:
        raise HTTPException(
            status_code=404,
            detail="Review not found"
        )

    return confidence_payload


@app.post("/reviews/{interpretation_id}/override")
def apply_review_human_override(
    interpretation_id: str,
    request: HumanOverrideRequest,
):
    override_payload = (
        ai_review_service
        .apply_human_override(
            interpretation_id=
                interpretation_id,
            overridden_by=
                request.overridden_by,
            override_reason=
                request.override_reason,
        )
    )

    if not override_payload:
        raise HTTPException(
            status_code=404,
            detail="Review not found"
        )

    return override_payload


@app.get("/reviews/analytics")
def get_review_analytics():
    return (
        ai_review_service
        .get_review_analytics()
    )


@app.get("/reviews/{interpretation_id}/explainability")
def get_review_explainability(
    interpretation_id: str,
):
    explainability_payload = (
        ai_review_service
        .get_review_explainability(
            interpretation_id
        )
    )

    if not explainability_payload:
        raise HTTPException(
            status_code=404,
            detail="Review not found"
        )

    return explainability_payload


@app.get("/reviews/{interpretation_id}/audit-logs")
def get_review_audit_logs(
    interpretation_id: str,
):
    audit_payload = (
        ai_review_service
        .get_review_audit_logs(
            interpretation_id
        )
    )

    if not audit_payload:
        raise HTTPException(
            status_code=404,
            detail="Review not found"
        )

    return audit_payload


@app.post("/reviews/{interpretation_id}/escalate")
def run_review_escalation(
    interpretation_id: str,
    force: bool = False,
):
    escalation_payload = (
        ai_review_service
        .run_review_escalation_logic(
            interpretation_id=
                interpretation_id,
            force=
                force,
        )
    )

    if not escalation_payload:
        raise HTTPException(
            status_code=404,
            detail="Review not found"
        )

    return escalation_payload


@app.post("/reviews/{interpretation_id}/recommendation/review")
def review_ai_recommendation(
    interpretation_id: str,
    request: RecommendationReviewRequest,
):
    try:
        payload = (
            ai_review_service
            .review_ai_recommendation(
                interpretation_id=
                    interpretation_id,
                decision=
                    request.decision,
                reviewed_by=
                    request.reviewed_by,
                review_notes=
                    request.review_notes,
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc)
        ) from exc

    if not payload:
        raise HTTPException(
            status_code=404,
            detail="Review not found"
        )

    return payload


@app.post("/reviews/{interpretation_id}/comments")
def add_review_comment(
    interpretation_id: str,
    request: ReviewCommentRequest,
):
    payload = (
        ai_review_service
        .add_review_comment(
            interpretation_id=
                interpretation_id,
            author=
                request.author,
            comment=
                request.comment,
        )
    )
    if not payload:
        raise HTTPException(
            status_code=404,
            detail="Review not found"
        )
    return payload


@app.get("/reviews/{interpretation_id}/comments")
def list_review_comments(
    interpretation_id: str,
):
    payload = (
        ai_review_service
        .list_review_comments(
            interpretation_id
        )
    )
    if not payload:
        raise HTTPException(
            status_code=404,
            detail="Review not found"
        )
    return payload


@app.post("/reviews/{interpretation_id}/notifications")
def send_review_notification(
    interpretation_id: str,
    request: ReviewNotificationRequest,
):
    payload = (
        ai_review_service
        .send_review_notification(
            interpretation_id=
                interpretation_id,
            recipient_id=
                request.recipient_id,
            message=
                request.message,
            channel=
                request.channel,
        )
    )
    if not payload:
        raise HTTPException(status_code=404, detail="Review not found")
    return payload


@app.get("/reviews/{interpretation_id}/notifications")
def list_review_notifications(
    interpretation_id: str,
):
    payload = (
        ai_review_service
        .list_review_notifications(
            interpretation_id
        )
    )
    if not payload:
        raise HTTPException(status_code=404, detail="Review not found")
    return payload


@app.post("/reviews/{interpretation_id}/manual-approval")
def create_manual_approval_workflow(
    interpretation_id: str,
    request: ManualApprovalRequest,
):
    payload = (
        ai_review_service
        .create_manual_approval_workflow(
            interpretation_id=
                interpretation_id,
            requested_by=
                request.requested_by,
            notes=
                request.notes,
        )
    )
    if not payload:
        raise HTTPException(status_code=404, detail="Review not found")
    return payload

@app.get("/organizations")
def get_organizations():

    return (
        organization_repository
        .get_all_organizations()
    )

@app.get("/profiles/{profile_id}")
def get_profile(profile_id: str):

    profile = (
        profile_service
        .get_profile(profile_id)
    )

    if not profile:

        raise HTTPException(
            status_code=404,
            detail="Profile not found"
        )

    return profile

@app.get("/profiles/{profile_id}/notifications")
def get_profile_notifications(profile_id: str, unread_only: bool = False):
    return notification_service.get_notifications(profile_id, unread_only=unread_only)


@app.post("/profiles/{profile_id}/notifications")
async def create_profile_notification(profile_id: str, request: NotificationCreateRequest):
    payload = notification_service.create_notification(
        profile_id=profile_id,
        title=request.title,
        message=request.message,
        notification_type=request.notification_type,
        channel=request.channel,
        channels=request.channels,
        category=request.category,
        priority=request.priority,
        banner=request.banner,
        max_attempts=request.max_attempts,
        force_fail_channels=request.force_fail_channels,
    )
    await notification_connection_manager.broadcast_notification(profile_id, payload)
    return payload


@app.websocket("/profiles/{profile_id}/notifications/stream")
async def stream_profile_notifications(profile_id: str, websocket: WebSocket):
    await notification_connection_manager.connect(profile_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        notification_connection_manager.disconnect(profile_id, websocket)


@app.get("/profiles/{profile_id}/notifications/unread")
def get_profile_unread_notifications(profile_id: str):
    items = notification_service.get_unread_notifications(profile_id)
    return {"profile_id": profile_id, "total": len(items), "items": items}


@app.get("/profiles/{profile_id}/notifications/digest")
def get_profile_notification_digest(profile_id: str):
    return notification_service.get_digest(profile_id)


@app.put("/profiles/{profile_id}/notifications/preferences")
def set_profile_notification_preferences(profile_id: str, request: NotificationPreferenceRequest):
    return notification_service.set_preferences(
        profile_id=profile_id,
        channels=request.channels,
        categories=request.categories,
    )


@app.get("/profiles/{profile_id}/notifications/preferences")
def get_profile_notification_preferences(profile_id: str):
    return notification_service.get_preferences(profile_id)


@app.get("/profiles/{profile_id}/notifications/categories")
def get_profile_notification_categories(profile_id: str):
    return notification_service.list_categories(profile_id)


@app.get("/profiles/{profile_id}/notification-center")
def get_notification_center(profile_id: str):
    return notification_service.get_notifications(profile_id, include_center=True)


@app.post("/profiles/{profile_id}/notifications/retry")
def retry_profile_notifications(profile_id: str):
    return notification_service.retry_pending_notifications(profile_id)


@app.patch("/profiles/{profile_id}/notifications/read-sync")
def sync_profile_notification_read_state(profile_id: str, request: NotificationReadSyncRequest):
    return notification_service.sync_read_state(profile_id, request.read_ids)


@app.post("/profiles/{profile_id}/notifications/escalation")
async def create_escalation_notification(profile_id: str, request: NotificationEscalationRequest):
    payload = notification_service.create_escalation_notification(
        profile_id=profile_id,
        title=request.title,
        message=request.message,
        escalation_level=request.escalation_level,
    )
    await notification_connection_manager.broadcast_notification(profile_id, payload)
    return payload


@app.get("/profiles/{profile_id}/notifications/delivery-log")
def get_profile_notification_delivery_log(profile_id: str):
    return notification_service.get_delivery_log(profile_id)


@app.post("/projects")
def create_project(request: CreateProjectRequest):
    return project_service.create_project(
        project_name=request.project_name,
        supervisor_name=request.supervisor_name,
        supervisor_email=request.supervisor_email,
        organization_id=request.organization_id,
        owner_id=request.owner_id,
        tags=request.tags,
    )


@app.patch("/projects/{project_id}")
def edit_project(project_id: str, request: EditProjectRequest):
    updated = project_service.edit_project(
        project_id,
        project_name=request.project_name,
        supervisor_name=request.supervisor_name,
        supervisor_email=request.supervisor_email,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Project not found")
    return updated


@app.post("/projects/{project_id}/archive")
def archive_project(project_id: str):
    archived = project_service.archive_project(project_id)
    if not archived:
        raise HTTPException(status_code=404, detail="Project not found")
    return archived


@app.delete("/projects/{project_id}")
def delete_project(project_id: str):
    deleted = project_service.delete_project(project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"deleted": True, "project_id": project_id}


@app.get("/projects/search")
def search_projects(query: str):
    return project_service.search_projects(query)


@app.get("/projects")
def filter_projects(
    status: str | None = None,
    owner_id: str | None = None,
    tag: str | None = None,
):
    return project_service.filter_projects(
        status=status,
        owner_id=owner_id,
        tag=tag,
    )


@app.patch("/projects/{project_id}/tags")
def update_project_tags(project_id: str, request: ProjectTagsRequest):
    updated = project_service.update_project_tags(project_id, request.tags)
    if not updated:
        raise HTTPException(status_code=404, detail="Project not found")
    return updated


@app.patch("/projects/{project_id}/owner")
def set_project_owner(project_id: str, request: ProjectOwnerRequest):
    updated = project_service.set_project_owner(project_id, request.owner_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Project not found")
    return updated


@app.patch("/projects/{project_id}/lifecycle")
def set_project_lifecycle(project_id: str, request: ProjectLifecycleRequest):
    updated = project_service.set_project_lifecycle_phase(
        project_id,
        request.lifecycle_phase,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Project not found")
    return updated


@app.get("/projects/{project_id}/dashboard-widgets")
def get_project_dashboard_widgets(project_id: str):
    widgets = project_service.get_dashboard_widgets(project_id)
    if not widgets:
        raise HTTPException(status_code=404, detail="Project not found")
    return widgets

@app.get("/projects/{project_id}/links")
def get_cross_project_links(project_id: str):
    links = project_service.get_cross_project_links(project_id)
    if not links:
        raise HTTPException(status_code=404, detail="Project not found")
    return links


@app.get("/projects/{project_id}/kpis")
def get_project_kpis(project_id: str):
    kpis = project_service.get_project_kpis(project_id)
    if not kpis:
        raise HTTPException(status_code=404, detail="Project not found")
    return kpis


@app.get("/projects/{project_id}/analytics")
def get_project_analytics(project_id: str):
    analytics = project_service.get_project_analytics(project_id)
    if not analytics:
        raise HTTPException(status_code=404, detail="Project not found")
    return analytics


@app.get("/projects/{project_id}/attachments")
def get_project_attachments(project_id: str):
    attachments = project_service.get_project_attachments(project_id)
    if attachments is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"project_id": project_id, "attachments": attachments}


@app.post("/projects/{project_id}/attachments")
def add_project_attachment(project_id: str, request: ProjectAttachmentRequest):
    attachment = project_service.add_project_attachment(
        project_id=project_id,
        filename=request.filename,
        uploaded_by=request.uploaded_by,
    )
    if not attachment:
        raise HTTPException(status_code=404, detail="Project not found")
    return attachment


@app.get("/projects/{project_id}/comments")
def get_project_comments(project_id: str):
    comments = project_service.get_project_comments(project_id)
    if comments is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"project_id": project_id, "comments": comments}


@app.post("/projects/{project_id}/comments")
def add_project_comment(project_id: str, request: ProjectCommentRequest):
    comment = project_service.add_project_comment(
        project_id=project_id,
        comment=request.comment,
        author=request.author,
    )
    if not comment:
        raise HTTPException(status_code=404, detail="Project not found")
    return comment


@app.post("/reports/upload")
async def upload_report(
    project_id: str = Form(...),
    file: UploadFile = File(...),
):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    upload_dir = Path("tmp_uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")
    target_path = upload_dir / f"{timestamp}_{file.filename or 'report'}"

    with target_path.open("wb") as target_file:
        shutil.copyfileobj(file.file, target_file)

    try:
        result = report_processing_service.process_uploaded_report(
            project_id=project_id,
            filename=file.filename or target_path.name,
            file_path=str(target_path),
        )
    finally:
        if target_path.exists():
            target_path.unlink()

    if not result.get("success", False):
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": result.get("error_code", "REPORT_PROCESSING_FAILED"),
                "message": result.get("error_message", "Report processing failed"),
            },
        )

    return result


@app.post("/reports/upload/bulk")
async def upload_reports_bulk(
    project_id: str = Form(...),
    files: list[UploadFile] = File(...),
):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    upload_dir = Path("tmp_uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    uploads: list[dict] = []

    try:
        for file in files:
            timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")
            target_path = upload_dir / f"{timestamp}_{file.filename or 'report'}"
            with target_path.open("wb") as target_file:
                shutil.copyfileobj(file.file, target_file)
            uploads.append(
                {
                    "filename": file.filename or target_path.name,
                    "file_path": str(target_path),
                }
            )

        return report_processing_service.process_bulk_uploaded_reports(
            project_id=project_id,
            uploads=uploads,
        )
    finally:
        for item in uploads:
            path = Path(item["file_path"])
            if path.exists():
                path.unlink()


@app.get("/projects/{project_id}/reports/upload-jobs/{job_id}")
def get_reports_bulk_upload_progress(project_id: str, job_id: str):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    progress = report_processing_service.get_bulk_upload_progress(project_id, job_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Bulk upload job not found")
    return progress


@app.get("/projects/{project_id}/reports/timeline")
def get_project_report_timeline(project_id: str):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return report_processing_service.get_project_report_timeline(project_id)


@app.get("/projects/{project_id}/reports/ai-insights")
def get_project_report_ai_insights(project_id: str, limit: int = 20):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return report_processing_service.get_project_report_ai_insights(project_id, limit=limit)


@app.post("/projects/{project_id}/reports/attachments")
def add_report_attachment(project_id: str, request: ReportAttachmentRequest):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    result = report_processing_service.add_report_attachment(
        project_id=project_id,
        report_id=request.report_id,
        filename=request.filename,
        uploaded_by=request.uploaded_by,
    )
    if result.get("success") is False:
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": result.get("error_code", "INVALID_ATTACHMENT"),
                "message": result.get("error_message", "Attachment payload is invalid"),
            },
        )
    return result


@app.get("/projects/{project_id}/reports/{report_id}/attachments")
def list_report_attachments(project_id: str, report_id: str):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    attachments = report_processing_service.list_report_attachments(report_id)
    return {"project_id": project_id, "report_id": report_id, "attachments": attachments}


@app.delete("/projects/{project_id}/reports/{report_id}/attachments/{attachment_id}")
def delete_report_attachment(project_id: str, report_id: str, attachment_id: str):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    deleted = report_processing_service.delete_report_attachment(
        project_id=project_id,
        report_id=report_id,
        attachment_id=attachment_id,
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Attachment not found")
    return {"deleted": True, "attachment_id": attachment_id}


@app.patch("/projects/{project_id}/reports/{report_id}/tags")
def update_report_tags(project_id: str, report_id: str, request: ReportTagsRequest):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return report_processing_service.update_report_tags(project_id, report_id, request.tags)


@app.get("/projects/{project_id}/reports/{report_id}/tags")
def list_report_tags(project_id: str, report_id: str):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"project_id": project_id, "report_id": report_id, "tags": report_processing_service.list_report_tags(report_id)}


@app.get("/projects/{project_id}/reports/search")
def search_reports(project_id: str, q: str | None = None, tag: str | None = None, classification: str | None = None, limit: int = 20):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if q is None and tag and not classification:
        return report_processing_service.search_reports_by_tag(project_id, tag)
    return report_processing_service.search_reports(
        project_id,
        query=q,
        tag=tag,
        classification=classification,
        limit=limit,
    )


@app.get("/projects/{project_id}/reports/index")
def list_project_report_index(project_id: str):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return report_processing_service.list_project_index_entries(project_id)


@app.get("/projects/{project_id}/reports/{report_id}/index")
def get_report_index_entry(project_id: str, report_id: str):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    entry = report_processing_service.get_report_index_entry(report_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Report index not found")
    if entry.get("project_id") != project_id:
        raise HTTPException(status_code=404, detail="Report index not found")
    return entry


@app.get("/projects/{project_id}/timeline")
def get_project_timeline(project_id: str):
    timeline = project_service.get_project_timeline(project_id)
    if not timeline:
        raise HTTPException(status_code=404, detail="Project not found")
    return timeline

@app.get("/projects/{project_id}/workspace")
def get_project_workspace(project_id: str):

    return (
        project_workspace_service
        .get_workspace(project_id)
    )


@app.get("/projects/{project_id}/workspace/activities")
def list_workspace_activities(
    project_id: str,
    activity_type: str | None = None,
    actor_id: str | None = None,
    search: str | None = None,
    before: str | None = None,
    limit: int = 50,
):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return workspace_activity_service.list_activities(
        project_id=project_id,
        activity_type=activity_type,
        actor_id=actor_id,
        search=search,
        before=before,
        limit=limit,
    )


@app.post("/projects/{project_id}/workspace/activities")
async def create_workspace_activity(project_id: str, request: WorkspaceActivityCreateRequest):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    activity = workspace_activity_service.create_activity(
        project_id=project_id,
        activity_type=request.activity_type,
        title=request.title,
        description=request.description,
        metadata=request.metadata,
        actor_id=request.actor_id,
    )
    await workspace_connection_manager.broadcast_activity(project_id, activity)
    return activity


@app.websocket("/projects/{project_id}/workspace/stream")
async def stream_workspace_activity(project_id: str, websocket: WebSocket):
    await workspace_connection_manager.connect(project_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        workspace_connection_manager.disconnect(project_id, websocket)


@app.get("/projects/{project_id}/workspace/activities/search")
def search_workspace_activities(project_id: str, q: str, limit: int = 50):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return workspace_activity_service.list_activities(
        project_id=project_id,
        search=q,
        limit=limit,
    )


@app.get("/projects/{project_id}/workspace/feed")
def get_workspace_dynamic_feed(project_id: str, since: str | None = None, limit: int = 50):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return workspace_activity_service.list_activities(
        project_id=project_id,
        before=since,
        limit=limit,
    )


@app.get("/projects/{project_id}/workspace/live-operational-feed")
def get_live_operational_feed(project_id: str, limit: int = 20):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    feed = workspace_activity_service.list_activities(project_id=project_id, limit=limit * 3)
    activities = [
        item
        for item in feed["activities"]
        if "ACTION" in item.get("activity_type", "")
        or "ESCALATION" in item.get("activity_type", "")
        or "OPERATIONAL" in item.get("activity_type", "")
    ][:limit]
    return {
        "project_id": project_id,
        "total": len(activities),
        "activities": activities,
    }


@app.get("/projects/{project_id}/workspace/analytics")
def get_workspace_analytics(project_id: str):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return workspace_activity_service.get_analytics(project_id)


@app.get("/projects/{project_id}/workspace/grouped")
def get_grouped_workspace_activities(project_id: str, group_by: str = "activity_type"):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return workspace_activity_service.group_activities(project_id, group_by=group_by)


@app.get("/projects/{project_id}/workspace/layout")
def get_workspace_layout(project_id: str, auth_context=Depends(get_auth_context)):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return workspace_activity_service.get_layout(project_id, auth_context.actor_user_id)


@app.put("/projects/{project_id}/workspace/layout")
def save_workspace_layout(project_id: str, request: WorkspaceLayoutRequest, auth_context=Depends(get_auth_context)):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return workspace_activity_service.save_layout(project_id, auth_context.actor_user_id, request.layout)


@app.get("/projects/{project_id}/workspace/widgets")
def get_workspace_widgets(project_id: str, auth_context=Depends(get_auth_context)):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return workspace_activity_service.get_widgets(project_id, auth_context.actor_user_id)


@app.put("/projects/{project_id}/workspace/widgets")
def save_workspace_widgets(project_id: str, request: WorkspaceWidgetsRequest, auth_context=Depends(get_auth_context)):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return workspace_activity_service.save_widgets(project_id, auth_context.actor_user_id, request.widgets)


@app.get("/projects/{project_id}/workspace/permissions")
def get_workspace_permissions(project_id: str, auth_context=Depends(get_auth_context)):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    can_edit = auth_context.role in {"MANAGER", "ADMIN"}
    return {
        "project_id": project_id,
        "user_id": auth_context.actor_user_id,
        "role": auth_context.role,
        "permissions": {
            "can_view": True,
            "can_edit_layout": can_edit,
            "can_customize_widgets": can_edit,
            "can_create_activity": can_edit,
        },
    }


@app.post("/workspace/cross-project")
def get_cross_project_workspace(request: CrossProjectWorkspaceRequest, _: object = Depends(require_permission("projects:read"))):
    valid_projects: list[str] = []
    for project_id in request.project_ids:
        project = project_repository.get_project_by_id(project_id)
        if project:
            valid_projects.append(project_id)
    return workspace_activity_service.list_cross_project_activities(valid_projects, limit=request.limit)

@app.get("/projects/{project_id}/exceptions")
def get_project_exceptions(project_id: str):

    return (
        operational_action_repository
        .get_exceptions_by_project(project_id)
    )


@app.get("/projects/{project_id}/actions/priorities")
def get_action_priorities(project_id: str):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return operational_action_service.get_action_priorities(project_id)


@app.get("/projects/{project_id}/actions/dependency-graph")
def get_action_dependency_graph(project_id: str):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return operational_action_service.get_dependency_graph(project_id)


@app.post("/projects/{project_id}/actions/recurring")
def create_recurring_action(project_id: str, request: ActionRecurringRequest):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return operational_action_service.create_recurring_action(
        project_id=project_id,
        title=request.title,
        recurrence_rule=request.recurrence_rule,
        created_by=request.created_by,
    )


@app.get("/projects/{project_id}/actions/recurring")
def list_recurring_actions(project_id: str):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return operational_action_service.list_recurring_actions(project_id)


@app.post("/projects/{project_id}/actions/bulk")
def bulk_create_actions(project_id: str, request: ActionBulkRequest):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return operational_action_service.bulk_create_actions(project_id, request.actions)


@app.post("/projects/{project_id}/actions/{action_id}/attachments")
def add_action_attachment(project_id: str, action_id: str, request: ActionAttachmentRequest):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return operational_action_service.add_attachment(action_id, request.filename, request.uploaded_by)


@app.get("/projects/{project_id}/actions/{action_id}/attachments")
def list_action_attachments(project_id: str, action_id: str):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"attachments": operational_action_service.list_attachments(action_id)}


@app.delete("/projects/{project_id}/actions/{action_id}/attachments/{attachment_id}")
def delete_action_attachment(project_id: str, action_id: str, attachment_id: str):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    deleted = operational_action_service.delete_attachment(action_id, attachment_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Attachment not found")
    return {"deleted": True}


@app.post("/projects/{project_id}/actions/{action_id}/notifications")
def create_action_notification(project_id: str, action_id: str, request: ActionNotificationRequest):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return operational_action_service.create_notification(
        action_id=action_id,
        recipient_id=request.recipient_id,
        message=request.message,
        channel=request.channel,
    )


@app.get("/projects/{project_id}/actions/{action_id}/notifications")
def list_action_notifications(project_id: str, action_id: str):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"notifications": operational_action_service.list_notifications(action_id)}


@app.get("/projects/{project_id}/actions/analytics")
def get_action_analytics(project_id: str):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return operational_action_service.get_action_analytics(project_id)


@app.post("/projects/{project_id}/actions/{action_id}/comments")
def add_action_comment(project_id: str, action_id: str, request: ActionCommentRequest):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return operational_action_service.add_comment(action_id, request.comment, request.created_by)


@app.get("/projects/{project_id}/actions/{action_id}/comments")
def list_action_comments(project_id: str, action_id: str):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"comments": operational_action_service.list_comments(action_id)}


@app.get("/projects/{project_id}/actions/{action_id}/history")
def get_action_history(project_id: str, action_id: str):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"history": operational_action_service.get_history(action_id)}


@app.get("/projects/{project_id}/actions/sla")
def get_action_sla_dashboard(project_id: str):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return operational_action_service.get_sla_dashboard(project_id)


@app.post("/projects/{project_id}/actions/{action_id}/retry")
def retry_action(project_id: str, action_id: str, request: ActionRetryRequest):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return operational_action_service.retry_action(action_id, request.reason)


@app.patch("/projects/{project_id}/actions/{action_id}/owner")
def set_action_owner(project_id: str, action_id: str, request: ActionOwnerRequest):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return operational_action_service.set_owner(action_id, request.owner_id)


@app.post("/projects/{project_id}/actions/{action_id}/escalate")
def escalate_action_with_hierarchy(project_id: str, action_id: str, request: ActionEscalationRequest):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return operational_action_service.escalate_with_hierarchy(action_id, request.level, request.reason)


@app.post("/projects/{project_id}/actions/ai-generate")
def generate_ai_actions(project_id: str, request: ActionAIGenerationRequest):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return operational_action_service.generate_ai_actions(project_id, request.context)


@app.post("/projects/{project_id}/actions/templates")
def create_action_template(project_id: str, request: ActionTemplateRequest):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return operational_action_service.create_template(
        project_id=project_id,
        name=request.name,
        title=request.title,
        description=request.description,
        category=request.category,
    )


@app.get("/projects/{project_id}/actions/templates")
def list_action_templates(project_id: str):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return operational_action_service.list_templates(project_id)


@app.post("/projects/{project_id}/actions/templates/{template_id}/apply")
def apply_action_template(project_id: str, template_id: str, request: ActionTemplateApplyRequest):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    payload = operational_action_service.apply_template(project_id, template_id, request.created_by)
    if not payload:
        raise HTTPException(status_code=404, detail="Action template not found")
    return payload


@app.patch("/projects/{project_id}/actions/{action_id}/category")
def categorize_action(project_id: str, action_id: str, request: ActionCategoryRequest):
    project = project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    payload = operational_action_service.categorize_action(action_id, request.category)
    if not payload:
        raise HTTPException(status_code=404, detail="Action not found")
    return payload

@app.get("/projects/{project_id}/operational-summary")
def get_project_operational_summary(project_id: str):

    return (
        operational_summary_service
        .generate_project_summary(project_id)
    )

@app.patch("/notifications/{notification_id}/read")
def mark_notification_as_read(notification_id: str):

    return (
        notification_service
        .mark_as_read(notification_id)
    )

# ==========================================
# AUTOMATION APIs
# ==========================================

@app.get(
    "/automation/runs"
)
def get_automation_runs():

    return (
        automation_monitoring_service
        .get_recent_runs()
    )


@app.get(
    "/automation/stats"
)
def get_automation_stats():

    return (
        automation_monitoring_service
        .get_automation_stats()
    )


@app.get(
    "/automation/health"
)
def get_automation_health():

    return (
        automation_monitoring_service
        .get_automation_health_dashboard()
    )


@app.get(
    "/automation/circuit-breakers"
)
def get_automation_circuit_breakers():

    return (
        automation_monitoring_service
        .get_circuit_breakers()
    )


@app.get("/automation/circuit-breakers/dashboard")
def get_circuit_breaker_dashboard():
    return circuit_breaker_dashboard_service.get_dashboard()


@app.get("/automation/circuit-breakers/metrics")
def get_circuit_breaker_metrics():
    breakers = circuit_breaker_service.list_breakers()
    return circuit_breaker_dashboard_service.analytics_service.get_metrics(
        breakers
    )


@app.get("/automation/circuit-breakers/analytics")
def get_circuit_breaker_analytics():
    breakers = circuit_breaker_service.list_breakers()
    return circuit_breaker_dashboard_service.analytics_service.get_analytics(
        breakers
    )


@app.get("/automation/circuit-breakers/thresholds")
def list_circuit_breaker_thresholds():
    return {
        "thresholds": circuit_breaker_threshold_service.list_thresholds(),
    }


@app.post("/automation/circuit-breakers/thresholds")
def set_circuit_breaker_threshold(request: CircuitBreakerThresholdRequest):
    threshold = circuit_breaker_threshold_service.set_threshold(
        breaker_key=request.breaker_key,
        failure_threshold=request.failure_threshold,
        cooldown_minutes=request.cooldown_minutes,
        half_open_success_threshold=request.half_open_success_threshold,
    )
    return {
        "breaker_key": request.breaker_key,
        "threshold": threshold,
    }


@app.post("/automation/circuit-breakers/{breaker_key}/reopen")
def reopen_circuit_breaker(
    breaker_key: str,
    request: CircuitBreakerReopenRequest,
):
    try:
        return circuit_breaker_reopen_service.manual_reopen(
            breaker_key=breaker_key,
            initiated_by=request.initiated_by,
            force_closed=request.force_closed,
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.get("/automation/circuit-breakers/degradation")
def get_service_degradation_mode():
    breakers = circuit_breaker_service.list_breakers()
    return circuit_breaker_dashboard_service.degradation_service.get_degradation_mode(
        breakers
    )


@app.get("/automation/circuit-breakers/health-scores")
def get_circuit_breaker_health_scores():
    breakers = circuit_breaker_service.list_breakers()
    return circuit_breaker_dashboard_service.health_scoring_service.get_overall_health_score(
        breakers
    )


@app.get("/automation/circuit-breakers/outages")
def get_circuit_breaker_outages():
    breakers = circuit_breaker_service.list_breakers()
    return circuit_breaker_dashboard_service.outage_service.get_outage_summary(
        breakers
    )


@app.get("/automation/circuit-breakers/dependencies")
def get_circuit_breaker_dependencies():
    breakers = circuit_breaker_service.list_breakers()
    return circuit_breaker_dashboard_service.dependency_service.get_dependency_summary(
        breakers
    )


@app.get("/automation/circuit-breakers/ai-failover")
def get_ai_provider_failover_status():
    return circuit_breaker_dashboard_service.failover_service.get_status()


@app.get(
    "/automation/ai-recovery"
)
def get_automation_ai_recovery():

    return (
        automation_monitoring_service
        .get_ai_recovery_monitoring()
    )


@app.get("/automation/dead-letters/dashboard")
def get_dead_letter_recovery_dashboard():
    return recovery_dashboard_service.get_dashboard()


@app.get("/automation/dead-letters")
def search_dead_letters(
    execution_type: str | None = None,
    failure_type: str | None = None,
    severity: str | None = None,
    project_id: str | None = None,
    query: str | None = None,
    limit: int = 50,
):
    return {
        "dead_letters": dead_letter_recovery_service.search_dead_letters(
            execution_type=execution_type,
            failure_type=failure_type,
            severity=severity,
            project_id=project_id,
            query=query,
            limit=limit,
        ),
    }


@app.get("/automation/dead-letters/metrics")
def get_dead_letter_recovery_metrics():
    return dead_letter_recovery_service.get_metrics()


@app.get("/automation/dead-letters/analytics")
def get_dead_letter_analytics():
    return dead_letter_recovery_service.get_analytics()


@app.get("/automation/dead-letters/audit-logs")
def get_recovery_audit_logs(
    execution_log_id: str | None = None,
    limit: int = 100,
):
    return {
        "entries": dead_letter_recovery_service.list_audit_logs(
            execution_log_id=execution_log_id,
            limit=limit,
        ),
    }


@app.get("/automation/dead-letters/replay-tracking")
def get_recovery_replay_tracking(
    execution_log_id: str | None = None,
    limit: int = 100,
):
    return {
        "replays": dead_letter_recovery_service.list_replay_tracking(
            execution_log_id=execution_log_id,
            limit=limit,
        ),
    }


@app.get("/automation/dead-letters/auto-recovery-rules")
def list_auto_recovery_rules():
    return {
        "rules": auto_recovery_rules_service.list_rules(),
    }


@app.post("/automation/dead-letters/search")
def post_search_dead_letters(request: DeadLetterSearchRequest):
    return {
        "dead_letters": dead_letter_recovery_service.search_dead_letters(
            execution_type=request.execution_type,
            failure_type=request.failure_type,
            severity=request.severity,
            project_id=request.project_id,
            query=request.query,
            limit=request.limit,
        ),
    }


@app.post("/automation/dead-letters/{log_id}/replay")
def replay_dead_letter_execution(
    log_id: str,
    request: RecoveryActionRequest,
):
    try:
        return dead_letter_recovery_service.replay_execution(
            log_id=log_id,
            initiated_by=request.initiated_by,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/automation/dead-letters/{log_id}/retry")
def retry_dead_letter_execution(
    log_id: str,
    request: RecoveryActionRequest,
):
    try:
        return dead_letter_recovery_service.retry_dead_letter(
            log_id=log_id,
            initiated_by=request.initiated_by,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/automation/dead-letters/{log_id}/manual-recover")
def manual_recover_dead_letter(
    log_id: str,
    request: RecoveryActionRequest,
):
    try:
        return dead_letter_recovery_service.manual_recover(
            log_id=log_id,
            initiated_by=request.initiated_by,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/automation/dead-letters/categorize-failure")
def categorize_dead_letter_failure(request: FailureCategorizationRequest):
    return dead_letter_recovery_service.categorize_failure(
        error_message=request.error_message,
    )


@app.post("/automation/dead-letters/orchestrate")
def orchestrate_dead_letter_recovery(request: RecoveryOrchestrationRequest):
    return recovery_orchestration_service.orchestrate_recovery_cycle(
        initiated_by=request.initiated_by,
        limit=request.limit,
    )


@app.get(
    "/automation/ai-execution-logs"
)
def get_automation_ai_execution_logs():

    return (
        automation_monitoring_service
        .get_ai_execution_logs_dashboard()
    )


@app.get(
    "/automation/schedules"
)
def get_automation_schedules():
    return {
        "jobs":
            automation_cron_management_service
            .list_job_schedules()
    }


@app.put(
    "/automation/schedules/{job_id}"
)
def update_automation_schedule(
    job_id: str,
    request: AutomationCronScheduleRequest,
):
    try:
        return (
            automation_cron_management_service
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


@app.patch(
    "/automation/schedules/{job_id}/status"
)
def set_automation_schedule_status(
    job_id: str,
    request: AutomationJobStatusRequest,
):
    try:
        return (
            automation_cron_management_service
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


@app.post(
    "/automation/runs/{run_id}/replay"
)
def replay_automation_run(
    run_id: str,
):
    try:
        return (
            automation_replay_service
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


@app.get(
    "/automation/control/status"
)
def get_automation_control_status():
    return (
        automation_control_service
        .get_status()
    )


@app.post(
    "/automation/control/pause"
)
def pause_automation_scheduler():
    return (
        automation_control_service
        .pause()
    )


@app.post(
    "/automation/control/resume"
)
def resume_automation_scheduler():
    return (
        automation_control_service
        .resume()
    )


@app.get("/automation/queue")
def list_automation_queue(status: str | None = None):
    return {
        "items": automation_job_queue_service.list_items(status=status),
    }


@app.post("/automation/queue")
def enqueue_automation_job(request: AutomationQueueRequest):
    return automation_job_queue_service.enqueue(
        job_name=request.job_name,
        payload=request.payload,
        priority=request.priority,
        idempotency_key=request.idempotency_key,
    )


@app.get("/automation/workers/stats")
def get_automation_worker_stats():
    return automation_worker_service.get_worker_stats()


@app.post("/automation/workers/process-next")
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
    return automation_worker_service.process_next(
        worker_id=request.worker_id,
        handlers=handlers,
    )


@app.get("/automation/retry-policies/{job_name}")
def get_automation_retry_policy(job_name: str):
    return automation_retry_policy_service.get_policy(job_name)


@app.put("/automation/retry-policies/{job_name}")
def set_automation_retry_policy(job_name: str, request: AutomationRetryPolicyRequest):
    return automation_retry_policy_service.set_policy(
        job_name=job_name,
        max_attempts=request.max_attempts,
        backoff_seconds=request.backoff_seconds,
        multiplier=request.multiplier,
    )


@app.post("/automation/retry-policies/{job_name}/evaluate")
def evaluate_automation_retry_policy(job_name: str, request: AutomationRetryEvaluationRequest):
    return automation_retry_policy_service.evaluate_retry(
        job_name=job_name,
        attempts=request.attempts,
    )


@app.post("/automation/scheduler/claim-tick")
def claim_automation_scheduler_tick(request: AutomationSchedulerClaimRequest):
    return automation_scheduler_guard_service.claim_tick(
        job_name=request.job_name,
        owner_id=request.owner_id,
        window_seconds=request.window_seconds,
    )


@app.post("/automation/governance/evaluate")
def evaluate_automation_governance(request: AutomationGovernanceRequest):
    return automation_governance_service.evaluate(
        job_name=request.job_name,
        payload=request.payload,
        actor=request.actor,
    )


@app.post("/automation/workflows/versions")
def create_workflow_version(request: WorkflowVersionCreateRequest):
    return workflow_versioning_service.create_version(
        workflow_name=request.workflow_name,
        definition=request.definition,
        published_by=request.published_by,
        activate=request.activate,
    )


@app.get("/automation/workflows/{workflow_name}/versions")
def list_workflow_versions(workflow_name: str):
    return {
        "workflow_name": workflow_name,
        "versions": workflow_versioning_service.list_versions(workflow_name),
    }


@app.get("/automation/workflows/{workflow_name}/active-version")
def get_active_workflow_version(workflow_name: str):
    active = workflow_versioning_service.get_active_version(workflow_name)
    if not active:
        raise HTTPException(status_code=404, detail="Workflow version not found")
    return active


@app.post("/automation/runs/{run_id}/logs")
def append_workflow_execution_log(run_id: str, request: WorkflowExecutionLogCreateRequest):
    return workflow_execution_log_service.append_log(
        run_id=run_id,
        level=request.level,
        message=request.message,
        context=request.context,
    )


@app.get("/automation/runs/{run_id}/logs")
def list_workflow_execution_logs(run_id: str, limit: int = 200):
    return {
        "run_id": run_id,
        "entries": workflow_execution_log_service.list_logs(
            run_id=run_id,
            limit=limit,
        ),
    }


@app.post("/automation/workflows/builder")
def build_dynamic_workflow(request: DynamicWorkflowBuilderRequest):
    try:
        return dynamic_automation_builder_service.build_workflow(
            workflow_name=request.workflow_name,
            steps=request.steps,
            created_by=request.created_by,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
