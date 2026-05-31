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

from app.services.portfolio_intelligence_dashboard_service import (
    PortfolioIntelligenceDashboardService,
)
from app.services.database_hardening_dashboard_service import (
    DatabaseHardeningDashboardService,
)
from app.services.devops_deployment_dashboard_service import (
    DevopsDeploymentDashboardService,
)
from app.services.security_dashboard_service import (
    SecurityDashboardService,
)
from app.services.observability_dashboard_service import (
    ObservabilityDashboardService,
)
from app.services.testing_dashboard_service import (
    TestingDashboardService,
)
from app.services.product_readiness_dashboard_service import (
    ProductReadinessDashboardService,
)
from app.services.future_ai_features_dashboard_service import (
    FutureAiFeaturesDashboardService,
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
        "/auth/exchange",
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

portfolio_intelligence_dashboard_service = (
    PortfolioIntelligenceDashboardService(
        portfolio_insights_service=portfolio_insights_service,
    )
)

database_hardening_dashboard_service = (
    DatabaseHardeningDashboardService()
)

devops_deployment_dashboard_service = (
    DevopsDeploymentDashboardService()
)

security_dashboard_service = (
    SecurityDashboardService()
)

observability_dashboard_service = (
    ObservabilityDashboardService()
)

testing_dashboard_service = (
    TestingDashboardService()
)

product_readiness_dashboard_service = (
    ProductReadinessDashboardService()
)

future_ai_features_dashboard_service = (
    FutureAiFeaturesDashboardService()
)

alert_engine_service = (
    AlertEngineService(
        portfolio_service=portfolio_insights_service,
    )
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


class ExchangeTokenRequest(
    BaseModel
):
    user_id: str


class ApproveReviewRequest(
    BaseModel
):
    reviewed_by: str
    review_notes: str | None = None


class RejectReviewRequest(
    BaseModel
):
    reviewed_by: str
    review_notes: str | None = None


class ActionAssignRequest(
    BaseModel
):
    assigned_to: str


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


@app.post("/auth/exchange")
def exchange_supabase_session(request: ExchangeTokenRequest):
    profile = profile_service.get_profile(request.user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    org_id = str(profile.get("organization_id") or "").strip()
    role = str(profile.get("role") or "VIEWER").strip().upper()
    if not org_id:
        raise HTTPException(status_code=422, detail="Profile missing organization_id")

    access_token = jwt_service.issue_access_token(
        user_id=request.user_id,
        org_id=org_id,
        role=role,
        token_id=f"exchange-{request.user_id}",
    )
    logger.info(
        "Supabase session exchanged for API token",
        extra={
            "event": "audit.login",
            "user_id": request.user_id,
            "org_id": org_id,
            "role": role,
        },
    )
    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "org_id": org_id,
        "role": role,
    }

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


@app.post("/reviews/{interpretation_id}/approve")
async def approve_review(
    interpretation_id: str,
    request: ApproveReviewRequest,
):
    payload = (
        ai_review_service
        .approve_review(
            interpretation_id=
                interpretation_id,
            reviewed_by=
                request.reviewed_by,
            review_notes=
                request.review_notes or "",
        )
    )

    if not payload:
        raise HTTPException(
            status_code=404,
            detail="Review not found"
        )

    created_action = payload.get("created_action") or {}
    notification_service.create_notification(
        profile_id=request.reviewed_by,
        title="ביקורת AI אושרה",
        message=(
            f"נוצרה פעולה תפעולית: "
            f"{created_action.get('title', 'פעולה חדשה')}"
        ),
        notification_type="REVIEW_APPROVED",
    )

    return payload


@app.post("/reviews/{interpretation_id}/reject")
def reject_review(
    interpretation_id: str,
    request: RejectReviewRequest,
):
    payload = (
        ai_review_service
        .reject_review(
            interpretation_id=
                interpretation_id,
            reviewed_by=
                request.reviewed_by,
            review_notes=
                request.review_notes,
        )
    )

    if not payload:
        raise HTTPException(
            status_code=404,
            detail="Review not found"
        )

    return payload


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


# ==========================================
# FLAT ACTION APIs (frontend convenience)
# ==========================================


@app.get("/actions/open")
def get_open_actions():
    return operational_action_service.get_open_actions()


@app.get("/actions/escalations")
def get_action_escalations():
    return operational_action_service.get_escalations()


@app.get("/actions/{action_id}")
def get_action_details(action_id: str):
    payload = operational_action_service.get_action_details(action_id)
    if not payload.get("success"):
        raise HTTPException(status_code=404, detail="Action not found")
    return payload


@app.get("/actions/{action_id}/comments")
def list_action_comments(action_id: str):
    action = operational_action_repository.get_action_by_id(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return {"comments": operational_action_service.list_comments(action_id)}


@app.post("/actions/{action_id}/comments")
def create_action_comment(action_id: str, request: ActionCommentRequest):
    action = operational_action_repository.get_action_by_id(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return operational_action_service.add_comment(
        action_id,
        request.comment,
        request.created_by,
    )


@app.post("/actions/{action_id}/close")
def close_action(action_id: str):
    action = operational_action_repository.get_action_by_id(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return operational_action_service.close_action(action_id)


@app.post("/actions/{action_id}/start")
def start_action(action_id: str):
    action = operational_action_repository.get_action_by_id(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return operational_action_service.start_action(action_id)


@app.post("/actions/{action_id}/block")
def block_action(action_id: str):
    action = operational_action_repository.get_action_by_id(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return operational_action_service.block_action(action_id)


@app.post("/actions/{action_id}/complete")
def complete_action(action_id: str):
    action = operational_action_repository.get_action_by_id(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return operational_action_service.complete_action(action_id)


@app.post("/actions/{action_id}/escalate")
def escalate_action(action_id: str):
    action = operational_action_repository.get_action_by_id(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return operational_action_service.escalate_action(action_id)


@app.post("/actions/{action_id}/assign")
def assign_action(action_id: str, request: ActionAssignRequest):
    action = operational_action_repository.get_action_by_id(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return operational_action_service.assign_action(
        action_id,
        request.assigned_to,
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


# ==========================================
# PORTFOLIO INTELLIGENCE
# ==========================================


@app.get("/portfolio/summary")
def get_portfolio_summary():
    return portfolio_intelligence_dashboard_service.get_summary()


@app.get("/portfolio/dashboard")
def get_portfolio_intelligence_dashboard(
    organization_id: str | None = None,
):
    return portfolio_intelligence_dashboard_service.get_dashboard(
        organization_id=organization_id,
    )


@app.get("/portfolio/trends")
def get_portfolio_trends():
    return portfolio_intelligence_dashboard_service.get_trends()


@app.get("/portfolio/predictive-risk")
def get_portfolio_predictive_risk():
    return portfolio_intelligence_dashboard_service.get_predictive_risk()


@app.get("/portfolio/executive-kpis")
def get_portfolio_executive_kpis():
    return portfolio_intelligence_dashboard_service.get_executive_kpis()


@app.get("/portfolio/forecast")
def get_portfolio_forecast(horizon_days: int = 30):
    return portfolio_intelligence_dashboard_service.get_forecast(
        horizon_days=horizon_days,
    )


@app.get("/portfolio/heatmap")
def get_portfolio_heatmap():
    return portfolio_intelligence_dashboard_service.get_heatmap()


@app.get("/portfolio/benchmarks")
def get_portfolio_benchmarks(organization_id: str | None = None):
    return portfolio_intelligence_dashboard_service.get_benchmarks(
        organization_id=organization_id,
    )


@app.get("/portfolio/recommendations")
def get_portfolio_recommendations():
    return portfolio_intelligence_dashboard_service.get_recommendations()


@app.get("/portfolio/analytics")
def get_portfolio_analytics():
    return portfolio_intelligence_dashboard_service.get_analytics()


@app.get("/portfolio/metrics")
def get_portfolio_metrics():
    return portfolio_intelligence_dashboard_service.get_metrics()


@app.get("/portfolio/risk-scores")
def get_portfolio_risk_scores():
    return portfolio_intelligence_dashboard_service.get_risk_scores()


@app.get("/portfolio/predictive-alerts")
def get_portfolio_predictive_alerts():
    return portfolio_intelligence_dashboard_service.get_predictive_alerts()


@app.get("/portfolio/executive-summary")
def get_portfolio_executive_summary():
    return portfolio_intelligence_dashboard_service.get_executive_summary()


@app.get("/portfolio/cross-organization")
def get_portfolio_cross_organization_insights():
    return (
        portfolio_intelligence_dashboard_service
        .get_cross_organization_insights()
    )


# ==========================================
# DATABASE HARDENING
# ==========================================


@app.get("/database/dashboard")
def get_database_hardening_dashboard():
    return database_hardening_dashboard_service.get_dashboard()


@app.get("/database/migrations")
def list_database_migrations():
    return database_hardening_dashboard_service.get_migrations()


@app.get("/database/migrations/status")
def get_database_migration_status():
    return database_hardening_dashboard_service.get_migration_status()


@app.post("/database/migrations/apply")
def apply_database_migrations():
    return database_hardening_dashboard_service.apply_migrations()


@app.get("/database/rls/policies")
def list_database_rls_policies():
    return database_hardening_dashboard_service.get_rls_policies()


@app.get("/database/rls/validate")
def validate_database_rls():
    return database_hardening_dashboard_service.validate_rls()


@app.get("/database/foreign-keys")
def list_database_foreign_keys():
    return database_hardening_dashboard_service.get_foreign_keys()


@app.get("/database/foreign-keys/validate")
def validate_database_foreign_keys():
    return database_hardening_dashboard_service.validate_foreign_keys()


@app.get("/database/indexes")
def list_database_indexes():
    return database_hardening_dashboard_service.get_indexes()


@app.get("/database/indexes/recommendations")
def get_database_index_recommendations():
    return database_hardening_dashboard_service.get_index_recommendations()


@app.get("/database/soft-delete/tables")
def list_soft_delete_tables():
    return database_hardening_dashboard_service.get_soft_delete_tables()


@app.get("/database/audit/tables")
def list_audit_tables():
    return database_hardening_dashboard_service.get_audit_tables()


@app.get("/database/audit/log")
def get_database_audit_log(
    table_name: str | None = None,
    organization_id: str | None = None,
    limit: int = 100,
):
    return database_hardening_dashboard_service.get_audit_log(
        table_name=table_name,
        organization_id=organization_id,
        limit=limit,
    )


@app.get("/database/backup/strategy")
def get_database_backup_strategy():
    return database_hardening_dashboard_service.get_backup_strategy()


@app.get("/database/backup/status")
def get_database_backup_status():
    return database_hardening_dashboard_service.get_backup_status()


@app.post("/database/backup/restore-test")
def run_database_backup_restore_test(backup_id: str = "latest"):
    return database_hardening_dashboard_service.run_backup_restore_test(
        backup_id=backup_id,
    )


@app.get("/database/monitoring/health")
def get_database_monitoring_health():
    return database_hardening_dashboard_service.get_monitoring_health()


@app.get("/database/monitoring/metrics")
def get_database_monitoring_metrics():
    return database_hardening_dashboard_service.get_monitoring_metrics()


@app.get("/database/monitoring/alerts")
def get_database_monitoring_alerts():
    return database_hardening_dashboard_service.get_monitoring_alerts()


@app.get("/database/seeds")
def list_database_seed_scripts():
    return database_hardening_dashboard_service.get_seed_scripts()


@app.post("/database/seeds/demo")
def generate_database_demo_seed():
    return database_hardening_dashboard_service.generate_demo_seed()


@app.get("/database/fixtures/types")
def list_database_fixture_types():
    return database_hardening_dashboard_service.get_fixture_types()


@app.post("/database/fixtures/test-suite")
def build_database_test_fixtures(organization_id: str = "org-fixture-1"):
    return database_hardening_dashboard_service.build_test_fixtures(
        organization_id=organization_id,
    )


@app.get("/database/query-optimization")
def get_database_query_optimization_report():
    return database_hardening_dashboard_service.get_query_optimization_report()


@app.get("/database/connection-pool/config")
def get_database_connection_pool_config():
    return database_hardening_dashboard_service.get_connection_pool_config()


@app.get("/database/connection-pool/stats")
def get_database_connection_pool_stats():
    return database_hardening_dashboard_service.get_connection_pool_stats()


@app.get("/database/tenant-isolation")
def get_database_tenant_isolation_report():
    return database_hardening_dashboard_service.get_tenant_isolation_report()


@app.get("/database/retention/policies")
def list_database_retention_policies():
    return database_hardening_dashboard_service.get_retention_policies()


# ==========================================
# DEVOPS & DEPLOYMENT
# ==========================================


@app.get("/devops/dashboard")
def get_devops_dashboard():
    return devops_deployment_dashboard_service.get_dashboard()


@app.get("/devops/docker/images")
def list_devops_docker_images():
    return devops_deployment_dashboard_service.get_docker_images()


@app.get("/devops/docker/validate")
def validate_devops_dockerfiles():
    return devops_deployment_dashboard_service.validate_dockerfiles()


@app.get("/devops/docker/build")
def get_devops_docker_build_instructions(image_name: str = "orgflow-api"):
    return devops_deployment_dashboard_service.get_docker_build_instructions(
        image_name,
    )


@app.get("/devops/compose/stack")
def get_devops_compose_stack():
    return devops_deployment_dashboard_service.get_compose_stack()


@app.get("/devops/compose/validate")
def validate_devops_compose():
    return devops_deployment_dashboard_service.validate_compose()


@app.get("/devops/compose/commands")
def get_devops_compose_commands():
    return devops_deployment_dashboard_service.get_compose_commands()


@app.get("/devops/environments")
def list_devops_environment_profiles():
    return devops_deployment_dashboard_service.get_environment_profiles()


@app.get("/devops/environments/{environment}")
def get_devops_environment_profile(environment: str):
    return devops_deployment_dashboard_service.get_environment_profile(
        environment,
    )


@app.get("/devops/environments/production/validate")
def validate_devops_production_environment():
    return devops_deployment_dashboard_service.validate_production_environment()


@app.get("/devops/cicd/pipeline")
def get_devops_cicd_pipeline():
    return devops_deployment_dashboard_service.get_cicd_pipeline()


@app.get("/devops/cicd/status")
def get_devops_cicd_status():
    return devops_deployment_dashboard_service.get_cicd_status()


@app.get("/devops/cicd/validate")
def validate_devops_cicd_pipeline():
    return devops_deployment_dashboard_service.validate_cicd_pipeline()


@app.get("/devops/github/workflows")
def list_devops_github_workflows():
    return devops_deployment_dashboard_service.get_github_workflows()


@app.get("/devops/github/validate")
def validate_devops_github_workflows():
    return devops_deployment_dashboard_service.validate_github_workflows()


@app.get("/devops/staging/config")
def get_devops_staging_config():
    return devops_deployment_dashboard_service.get_staging_config()


@app.get("/devops/staging/status")
def get_devops_staging_status():
    return devops_deployment_dashboard_service.get_staging_status()


@app.get("/devops/staging/validate")
def validate_devops_staging():
    return devops_deployment_dashboard_service.validate_staging()


@app.get("/devops/production/config")
def get_devops_production_config():
    return devops_deployment_dashboard_service.get_production_config()


@app.get("/devops/production/status")
def get_devops_production_status():
    return devops_deployment_dashboard_service.get_production_status()


@app.get("/devops/production/plan")
def plan_devops_production_deployment(version: str = "latest"):
    return devops_deployment_dashboard_service.plan_production_deployment(
        version,
    )


@app.get("/devops/production/validate")
def validate_devops_production():
    return devops_deployment_dashboard_service.validate_production()


@app.get("/devops/nginx/config")
def get_devops_nginx_config():
    return devops_deployment_dashboard_service.get_nginx_config()


@app.get("/devops/nginx/validate")
def validate_devops_nginx():
    return devops_deployment_dashboard_service.validate_nginx()


@app.get("/devops/nginx/routes")
def get_devops_nginx_routes():
    return devops_deployment_dashboard_service.get_nginx_routes()


@app.get("/devops/https/config")
def get_devops_https_config():
    return devops_deployment_dashboard_service.get_https_config()


@app.get("/devops/https/certificates")
def get_devops_https_certificate_status():
    return devops_deployment_dashboard_service.get_https_certificate_status()


@app.get("/devops/https/validate")
def validate_devops_https():
    return devops_deployment_dashboard_service.validate_https()


@app.get("/devops/cdn/config")
def get_devops_cdn_config():
    return devops_deployment_dashboard_service.get_cdn_config()


@app.get("/devops/cdn/rules")
def get_devops_cdn_cache_rules():
    return devops_deployment_dashboard_service.get_cdn_cache_rules()


@app.get("/devops/cdn/validate")
def validate_devops_cdn():
    return devops_deployment_dashboard_service.validate_cdn()


@app.get("/devops/caching/config")
def get_devops_caching_config():
    return devops_deployment_dashboard_service.get_caching_config()


@app.get("/devops/caching/validate")
def validate_devops_caching():
    return devops_deployment_dashboard_service.validate_caching()


@app.get("/devops/caching/stats")
def get_devops_caching_stats():
    return devops_deployment_dashboard_service.get_caching_stats()


@app.get("/devops/scaling/horizontal/config")
def get_devops_horizontal_scaling_config():
    return devops_deployment_dashboard_service.get_horizontal_scaling_config()


@app.get("/devops/scaling/horizontal/status")
def get_devops_horizontal_scaling_status():
    return devops_deployment_dashboard_service.get_horizontal_scaling_status()


@app.get("/devops/scaling/horizontal/simulate")
def simulate_devops_horizontal_scaling(
    cpu_percent: float = 45.0,
    memory_percent: float = 52.0,
    current_replicas: int = 3,
):
    return devops_deployment_dashboard_service.simulate_horizontal_scaling(
        cpu_percent=cpu_percent,
        memory_percent=memory_percent,
        current_replicas=current_replicas,
    )


@app.get("/devops/scaling/workers/config")
def get_devops_worker_scaling_config():
    return devops_deployment_dashboard_service.get_worker_scaling_config()


@app.get("/devops/scaling/workers/status")
def get_devops_worker_scaling_status():
    return devops_deployment_dashboard_service.get_worker_scaling_status()


@app.get("/devops/scaling/workers/simulate")
def simulate_devops_worker_scaling(
    queue_depth: int = 35,
    active_workers: int = 2,
):
    return devops_deployment_dashboard_service.simulate_worker_scaling(
        queue_depth=queue_depth,
        active_workers=active_workers,
    )


@app.get("/devops/monitoring/stack")
def get_devops_monitoring_stack():
    return devops_deployment_dashboard_service.get_monitoring_stack()


@app.get("/devops/monitoring/validate")
def validate_devops_monitoring_stack():
    return devops_deployment_dashboard_service.validate_monitoring_stack()


@app.get("/devops/monitoring/metrics")
def get_devops_monitoring_metrics():
    return devops_deployment_dashboard_service.get_monitoring_metrics()


@app.get("/devops/uptime/checks")
def list_devops_uptime_checks():
    return devops_deployment_dashboard_service.get_uptime_checks()


@app.get("/devops/uptime/status")
def get_devops_uptime_status():
    return devops_deployment_dashboard_service.get_uptime_status()


@app.get("/devops/logging/config")
def get_devops_logging_config():
    return devops_deployment_dashboard_service.get_logging_config()


@app.get("/devops/logging/streams")
def get_devops_log_streams():
    return devops_deployment_dashboard_service.get_log_streams()


@app.get("/devops/logging/validate")
def validate_devops_logging():
    return devops_deployment_dashboard_service.validate_logging()


@app.get("/devops/logging/search")
def search_devops_logs(
    query: str = "",
    level: str | None = None,
    limit: int = 100,
):
    return devops_deployment_dashboard_service.search_logs(
        query=query,
        level=level,
        limit=limit,
    )


@app.get("/devops/disaster-recovery/plan")
def get_devops_disaster_recovery_plan():
    return devops_deployment_dashboard_service.get_disaster_recovery_plan()


@app.get("/devops/disaster-recovery/rto-rpo")
def get_devops_disaster_recovery_rto_rpo():
    return devops_deployment_dashboard_service.get_disaster_recovery_rto_rpo()


@app.post("/devops/disaster-recovery/drill")
def run_devops_disaster_recovery_drill(scenario: str = "API_OUTAGE"):
    return devops_deployment_dashboard_service.run_disaster_recovery_drill(
        scenario,
    )


@app.get("/devops/rollout/checklist")
def get_devops_rollout_checklist():
    return devops_deployment_dashboard_service.get_rollout_checklist()


@app.get("/devops/rollout/evaluate")
def evaluate_devops_rollout_checklist(
    completed_ids: str | None = None,
):
    ids = completed_ids.split(",") if completed_ids else None
    return devops_deployment_dashboard_service.evaluate_rollout_checklist(ids)


@app.get("/devops/readiness/framework")
def get_devops_readiness_framework():
    return devops_deployment_dashboard_service.get_readiness_framework()


@app.get("/devops/readiness/review")
def run_devops_readiness_review(passed_checks: str | None = None):
    checks = passed_checks.split(",") if passed_checks else None
    return devops_deployment_dashboard_service.run_readiness_review(checks)


@app.get("/devops/readiness/blockers")
def get_devops_readiness_blockers(passed_checks: str | None = None):
    checks = passed_checks.split(",") if passed_checks else None
    return devops_deployment_dashboard_service.get_readiness_blockers(checks)


# ==========================================
# SECURITY
# ==========================================


@app.get("/security/dashboard")
def get_security_dashboard():
    return security_dashboard_service.get_dashboard()


@app.get("/security/rate-limiting/config")
def get_security_rate_limiting_config():
    return security_dashboard_service.get_rate_limiting_config()


@app.get("/security/rate-limiting/check")
def check_security_rate_limit(
    client_id: str = "default",
    tier: str = "authenticated",
    current_count: int = 0,
):
    return security_dashboard_service.check_rate_limit(
        client_id=client_id,
        tier=tier,
        current_count=current_count,
    )


@app.get("/security/rate-limiting/validate")
def validate_security_rate_limiting():
    return security_dashboard_service.validate_rate_limiting()


@app.get("/security/cors/recommendations")
def get_security_cors_recommendations():
    return security_dashboard_service.get_cors_recommendations()


@app.get("/security/cors/evaluate")
def evaluate_security_cors(allow_origins: str | None = None):
    origins = allow_origins.split(",") if allow_origins else None
    return security_dashboard_service.evaluate_cors(allow_origins=origins)


@app.get("/security/cors/validate")
def validate_security_cors():
    return security_dashboard_service.validate_cors()


@app.get("/security/secrets")
def list_security_managed_secrets():
    return security_dashboard_service.list_managed_secrets()


@app.get("/security/secrets/validate")
def validate_security_secrets_hygiene():
    return security_dashboard_service.validate_secrets_hygiene()


@app.get("/security/secrets/rotation-policy")
def get_security_secrets_rotation_policy():
    return security_dashboard_service.get_secrets_rotation_policy()


@app.get("/security/sql-injection/checklist")
def get_security_sql_injection_checklist():
    return security_dashboard_service.get_sql_injection_checklist()


@app.get("/security/sql-injection/scan")
def scan_security_sql_input(value: str = ""):
    return security_dashboard_service.scan_sql_input(value)


@app.get("/security/sql-injection/validate")
def validate_security_sql_posture():
    return security_dashboard_service.validate_sql_posture()


@app.get("/security/uploads/policy")
def get_security_file_upload_policy():
    return security_dashboard_service.get_file_upload_policy()


@app.get("/security/uploads/validate")
def validate_security_file_upload(
    filename: str = "report.pdf",
    size_bytes: int | None = None,
):
    return security_dashboard_service.validate_file_upload(
        filename=filename,
        size_bytes=size_bytes,
    )


@app.get("/security/malware/config")
def get_security_malware_scanner_config():
    return security_dashboard_service.get_malware_scanner_config()


@app.get("/security/malware/validate")
def validate_security_malware_scanner():
    return security_dashboard_service.validate_malware_scanner()


@app.get("/security/auth/controls")
def get_security_auth_hardening_controls():
    return security_dashboard_service.get_auth_hardening_controls()


@app.get("/security/auth/token-policy")
def evaluate_security_token_policy(
    access_token_ttl_minutes: int = 15,
    refresh_token_ttl_days: int = 7,
):
    return security_dashboard_service.evaluate_token_policy(
        access_token_ttl_minutes=access_token_ttl_minutes,
        refresh_token_ttl_days=refresh_token_ttl_days,
    )


@app.get("/security/auth/validate")
def validate_security_auth_hardening():
    return security_dashboard_service.validate_auth_hardening()


@app.get("/security/audit/events")
def get_security_audit_events():
    return security_dashboard_service.get_security_audit_events()


@app.get("/security/audit/coverage")
def get_security_audit_coverage():
    return security_dashboard_service.get_audit_coverage()


@app.get("/security/audit/validate")
def validate_security_audit_logging():
    return security_dashboard_service.validate_security_audit_logging()


@app.get("/security/permissions/matrix")
def get_security_permissions_matrix():
    return security_dashboard_service.get_permissions_matrix()


@app.get("/security/permissions/validate")
def validate_security_permissions_matrix():
    return security_dashboard_service.validate_permissions_matrix()


@app.get("/security/permissions/check")
def check_security_role_permission(
    role: str = "VIEWER",
    required_permission: str = "projects:read",
):
    return security_dashboard_service.validate_role_permission(
        role=role,
        required_permission=required_permission,
    )


@app.get("/security/owasp/assessment")
def get_security_owasp_assessment():
    return security_dashboard_service.get_owasp_assessment()


@app.get("/security/owasp/controls/{control_id}")
def evaluate_security_owasp_control(control_id: str):
    return security_dashboard_service.evaluate_owasp_control(control_id)


@app.get("/security/owasp/validate")
def validate_security_owasp_review():
    return security_dashboard_service.validate_owasp_review()


@app.get("/security/dependencies/lock-files")
def list_security_dependency_lock_files():
    return security_dashboard_service.list_dependency_lock_files()


@app.get("/security/dependencies/scan")
def simulate_security_dependency_scan(
    critical: int = 0,
    high: int = 0,
):
    return security_dashboard_service.simulate_dependency_scan(
        critical=critical,
        high=high,
    )


@app.get("/security/dependencies/validate")
def validate_security_dependency_scanning():
    return security_dashboard_service.validate_dependency_scanning()


@app.get("/security/supply-chain/controls")
def get_security_supply_chain_controls():
    return security_dashboard_service.get_supply_chain_controls()


@app.get("/security/supply-chain/validate")
def validate_security_supply_chain():
    return security_dashboard_service.validate_supply_chain()


@app.get("/security/supply-chain/sbom")
def get_security_sbom_status():
    return security_dashboard_service.get_sbom_status()


@app.get("/security/pentest/scenarios")
def list_security_pentest_scenarios():
    return security_dashboard_service.list_pentest_scenarios()


@app.post("/security/pentest/run")
def run_security_pentest_scenario(scenario_id: str = "AUTH_BYPASS"):
    return security_dashboard_service.run_pentest_scenario(scenario_id)


@app.post("/security/pentest/smoke")
def run_security_pentest_smoke_suite():
    return security_dashboard_service.run_pentest_smoke_suite()


@app.get("/security/tenant-isolation/report")
def get_security_tenant_isolation_report():
    return security_dashboard_service.get_tenant_isolation_report()


@app.get("/security/tenant-isolation/validate")
def validate_security_tenant_isolation():
    return security_dashboard_service.validate_tenant_isolation()


@app.get("/security/tenant-isolation/check")
def check_security_tenant_access(
    table_name: str = "projects",
    requesting_org_id: str = "org-1",
):
    return security_dashboard_service.validate_tenant_access(
        table_name=table_name,
        record={"organization_id": requesting_org_id},
        requesting_org_id=requesting_org_id,
    )


@app.get("/security/abuse/config")
def get_security_api_abuse_config():
    return security_dashboard_service.get_api_abuse_config()


@app.get("/security/abuse/evaluate")
def evaluate_security_api_abuse(
    client_id: str = "client-1",
    requests_per_minute: int = 0,
    failed_auth_count: int = 0,
):
    return security_dashboard_service.evaluate_api_abuse(
        client_id=client_id,
        requests_per_minute=requests_per_minute,
        failed_auth_count=failed_auth_count,
    )


@app.get("/security/abuse/validate")
def validate_security_api_abuse_protection():
    return security_dashboard_service.validate_api_abuse_protection()


# ==========================================
# OBSERVABILITY
# ==========================================


@app.get("/observability/dashboard")
def get_observability_dashboard():
    return observability_dashboard_service.get_dashboard()


@app.get("/observability/logging/config")
def get_observability_logging_config():
    return observability_dashboard_service.get_logging_config()


@app.get("/observability/logging/streams")
def get_observability_log_streams():
    return observability_dashboard_service.get_log_streams()


@app.get("/observability/logging/search")
def search_observability_logs(
    query: str = "",
    level: str | None = None,
    limit: int = 100,
):
    return observability_dashboard_service.search_logs(
        query=query,
        level=level,
        limit=limit,
    )


@app.get("/observability/logging/validate")
def validate_observability_logging():
    return observability_dashboard_service.validate_logging()


@app.get("/observability/metrics/config")
def get_observability_metrics_config():
    return observability_dashboard_service.get_metrics_config()


@app.get("/observability/metrics/catalog")
def get_observability_metrics_catalog():
    return observability_dashboard_service.get_metrics_catalog()


@app.get("/observability/metrics/snapshot")
def get_observability_metrics_snapshot(
    requests_total: int = 0,
    active_connections: int = 0,
    memory_bytes: int = 0,
):
    return observability_dashboard_service.get_metrics_snapshot(
        requests_total=requests_total,
        active_connections=active_connections,
        memory_bytes=memory_bytes,
    )


@app.get("/observability/metrics/validate")
def validate_observability_metrics():
    return observability_dashboard_service.validate_metrics()


@app.get("/observability/prometheus/config")
def get_observability_prometheus_config():
    return observability_dashboard_service.get_prometheus_config()


@app.get("/observability/prometheus/validate")
def validate_observability_prometheus():
    return observability_dashboard_service.validate_prometheus()


@app.get("/observability/prometheus/targets")
def get_observability_prometheus_targets():
    return observability_dashboard_service.get_prometheus_targets()


@app.get("/observability/grafana/config")
def get_observability_grafana_config():
    return observability_dashboard_service.get_grafana_config()


@app.get("/observability/grafana/dashboards")
def list_observability_grafana_dashboards():
    return observability_dashboard_service.list_grafana_dashboards()


@app.get("/observability/grafana/dashboards/{uid}")
def get_observability_grafana_dashboard(uid: str):
    return observability_dashboard_service.get_grafana_dashboard(uid)


@app.get("/observability/grafana/validate")
def validate_observability_grafana():
    return observability_dashboard_service.validate_grafana()


@app.get("/observability/ai-metrics/config")
def get_observability_ai_metrics_config():
    return observability_dashboard_service.get_ai_metrics_config()


@app.get("/observability/ai-metrics/catalog")
def get_observability_ai_metrics_catalog():
    return observability_dashboard_service.get_ai_metrics_catalog()


@app.get("/observability/ai-metrics/snapshot")
def get_observability_ai_metrics_snapshot(
    tokens_used: int = 0,
    avg_latency_ms: float = 0.0,
    error_rate: float = 0.0,
):
    return observability_dashboard_service.get_ai_metrics_snapshot(
        tokens_used=tokens_used,
        avg_latency_ms=avg_latency_ms,
        error_rate=error_rate,
    )


@app.get("/observability/ai-metrics/validate")
def validate_observability_ai_metrics():
    return observability_dashboard_service.validate_ai_metrics()


@app.get("/observability/automation-metrics/config")
def get_observability_automation_metrics_config():
    return observability_dashboard_service.get_automation_metrics_config()


@app.get("/observability/automation-metrics/catalog")
def get_observability_automation_metrics_catalog():
    return observability_dashboard_service.get_automation_metrics_catalog()


@app.get("/observability/automation-metrics/snapshot")
def get_observability_automation_metrics_snapshot(
    jobs_processed: int = 0,
    queue_depth: int = 0,
    success_rate: float = 100.0,
):
    return observability_dashboard_service.get_automation_metrics_snapshot(
        jobs_processed=jobs_processed,
        queue_depth=queue_depth,
        success_rate=success_rate,
    )


@app.get("/observability/automation-metrics/validate")
def validate_observability_automation_metrics():
    return observability_dashboard_service.validate_automation_metrics()


@app.get("/observability/sla/targets")
def get_observability_sla_targets():
    return observability_dashboard_service.get_sla_targets()


@app.get("/observability/sla/evaluate")
def evaluate_observability_sla(
    metric: str = "api_availability",
    actual_value: float = 99.95,
):
    return observability_dashboard_service.evaluate_sla(
        metric=metric,
        actual_value=actual_value,
    )


@app.get("/observability/sla/compliance")
def get_observability_sla_compliance():
    return observability_dashboard_service.get_sla_compliance()


@app.get("/observability/sla/validate")
def validate_observability_sla_metrics():
    return observability_dashboard_service.validate_sla_metrics()


@app.get("/observability/tracing/config")
def get_observability_tracing_config():
    return observability_dashboard_service.get_tracing_config()


@app.get("/observability/tracing/validate")
def validate_observability_tracing():
    return observability_dashboard_service.validate_tracing()


@app.get("/observability/alerting/config")
def get_observability_alerting_config():
    return observability_dashboard_service.get_alerting_config()


@app.get("/observability/alerting/rules")
def list_observability_alert_rules():
    return observability_dashboard_service.list_alert_rules()


@app.get("/observability/alerting/evaluate")
def evaluate_observability_alert_rule(
    rule_id: str = "HIGH_ERROR_RATE",
    current_value: float = 0.0,
):
    return observability_dashboard_service.evaluate_alert_rule(
        rule_id=rule_id,
        current_value=current_value,
    )


@app.get("/observability/alerting/validate")
def validate_observability_alerting():
    return observability_dashboard_service.validate_alerting()


@app.get("/observability/crashes/config")
def get_observability_crash_reporting_config():
    return observability_dashboard_service.get_crash_reporting_config()


@app.get("/observability/crashes/recent")
def get_observability_recent_crashes(limit: int = 10):
    return observability_dashboard_service.get_recent_crashes(limit=limit)


@app.get("/observability/crashes/validate")
def validate_observability_crash_reporting():
    return observability_dashboard_service.validate_crash_reporting()


@app.get("/observability/sentry/config")
def get_observability_sentry_config():
    return observability_dashboard_service.get_sentry_config()


@app.get("/observability/sentry/checklist")
def get_observability_sentry_checklist():
    return observability_dashboard_service.get_sentry_checklist()


@app.get("/observability/sentry/validate")
def validate_observability_sentry():
    return observability_dashboard_service.validate_sentry()


@app.get("/observability/runtime/snapshot")
def get_observability_runtime_snapshot():
    return observability_dashboard_service.get_runtime_snapshot()


@app.get("/observability/runtime/health")
def get_observability_runtime_health():
    return observability_dashboard_service.get_runtime_health()


@app.get("/observability/runtime/validate")
def validate_observability_runtime_diagnostics():
    return observability_dashboard_service.validate_runtime_diagnostics()


@app.get("/observability/performance/config")
def get_observability_performance_config():
    return observability_dashboard_service.get_performance_config()


@app.get("/observability/performance/evaluate")
def evaluate_observability_performance(
    p50_ms: float = 0.0,
    p95_ms: float = 0.0,
    p99_ms: float = 0.0,
    error_rate: float = 0.0,
    throughput_rps: float = 0.0,
):
    return observability_dashboard_service.evaluate_performance(
        p50_ms=p50_ms,
        p95_ms=p95_ms,
        p99_ms=p99_ms,
        error_rate=error_rate,
        throughput_rps=throughput_rps,
    )


@app.get("/observability/performance/summary")
def get_observability_performance_summary():
    return observability_dashboard_service.get_performance_summary()


@app.get("/observability/performance/validate")
def validate_observability_performance():
    return observability_dashboard_service.validate_performance()


@app.get("/testing/dashboard")
def get_testing_dashboard():
    return testing_dashboard_service.get_dashboard()


@app.get("/testing/unit/config")
def get_testing_unit_config():
    return testing_dashboard_service.get_unit_config()


@app.get("/testing/unit/suites")
def list_testing_unit_suites():
    return testing_dashboard_service.list_unit_suites()


@app.get("/testing/unit/coverage")
def evaluate_testing_unit_coverage(coverage_percent: float = 0.0):
    return testing_dashboard_service.evaluate_unit_coverage(
        coverage_percent=coverage_percent,
    )


@app.get("/testing/unit/validate")
def validate_testing_unit():
    return testing_dashboard_service.validate_unit_tests()


@app.get("/testing/integration/config")
def get_testing_integration_config():
    return testing_dashboard_service.get_integration_config()


@app.get("/testing/integration/scenarios")
def list_testing_integration_scenarios():
    return testing_dashboard_service.list_integration_scenarios()


@app.get("/testing/integration/validate")
def validate_testing_integration():
    return testing_dashboard_service.validate_integration_tests()


@app.get("/testing/api/config")
def get_testing_api_config():
    return testing_dashboard_service.get_api_config()


@app.get("/testing/api/endpoints")
def list_testing_api_endpoints():
    return testing_dashboard_service.list_api_endpoints()


@app.get("/testing/api/simulate")
def simulate_testing_api_request(
    method: str = "GET",
    path: str = "/health",
    status_code: int = 200,
):
    return testing_dashboard_service.simulate_api_request(
        method=method,
        path=path,
        status_code=status_code,
    )


@app.get("/testing/api/validate")
def validate_testing_api():
    return testing_dashboard_service.validate_api_tests()


@app.get("/testing/frontend/config")
def get_testing_frontend_config():
    return testing_dashboard_service.get_frontend_config()


@app.get("/testing/frontend/suites")
def list_testing_frontend_suites():
    return testing_dashboard_service.list_frontend_suites()


@app.get("/testing/frontend/validate")
def validate_testing_frontend():
    return testing_dashboard_service.validate_frontend_tests()


@app.get("/testing/playwright/config")
def get_testing_playwright_config():
    return testing_dashboard_service.get_playwright_config()


@app.get("/testing/playwright/flows")
def list_testing_playwright_flows():
    return testing_dashboard_service.list_playwright_flows()


@app.get("/testing/playwright/evaluate")
def evaluate_testing_playwright_flow(flow_id: str = "login"):
    return testing_dashboard_service.evaluate_playwright_flow(flow_id=flow_id)


@app.get("/testing/playwright/validate")
def validate_testing_playwright():
    return testing_dashboard_service.validate_playwright()


@app.get("/testing/automation/config")
def get_testing_automation_config():
    return testing_dashboard_service.get_automation_config()


@app.get("/testing/automation/tests")
def list_testing_automation_tests():
    return testing_dashboard_service.list_automation_tests()


@app.get("/testing/automation/validate")
def validate_testing_automation():
    return testing_dashboard_service.validate_automation_tests()


@app.get("/testing/ai-mock/config")
def get_testing_ai_mock_config():
    return testing_dashboard_service.get_ai_mock_config()


@app.get("/testing/ai-mock/fixtures")
def list_testing_ai_mock_fixtures():
    return testing_dashboard_service.list_ai_mock_fixtures()


@app.get("/testing/ai-mock/simulate")
def simulate_testing_ai_mock(
    provider: str = "openai",
    fixture_id: str = "review_summary",
):
    return testing_dashboard_service.simulate_ai_mock(
        provider=provider,
        fixture_id=fixture_id,
    )


@app.get("/testing/ai-mock/validate")
def validate_testing_ai_mock():
    return testing_dashboard_service.validate_ai_mock_tests()


@app.get("/testing/load/config")
def get_testing_load_config():
    return testing_dashboard_service.get_load_config()


@app.get("/testing/load/scenarios")
def list_testing_load_scenarios():
    return testing_dashboard_service.list_load_scenarios()


@app.get("/testing/load/evaluate")
def evaluate_testing_load(
    p95_ms: float = 0.0,
    error_rate_percent: float = 0.0,
):
    return testing_dashboard_service.evaluate_load_results(
        p95_ms=p95_ms,
        error_rate_percent=error_rate_percent,
    )


@app.get("/testing/load/validate")
def validate_testing_load():
    return testing_dashboard_service.validate_load_testing()


@app.get("/testing/recovery/config")
def get_testing_recovery_config():
    return testing_dashboard_service.get_recovery_config()


@app.get("/testing/recovery/scenarios")
def list_testing_recovery_scenarios():
    return testing_dashboard_service.list_recovery_scenarios()


@app.get("/testing/recovery/simulate")
def simulate_testing_recovery(scenario_id: str = "dlq_replay"):
    return testing_dashboard_service.simulate_recovery(scenario_id=scenario_id)


@app.get("/testing/recovery/validate")
def validate_testing_recovery():
    return testing_dashboard_service.validate_recovery_testing()


@app.get("/testing/chaos/config")
def get_testing_chaos_config():
    return testing_dashboard_service.get_chaos_config()


@app.get("/testing/chaos/experiments")
def list_testing_chaos_experiments():
    return testing_dashboard_service.list_chaos_experiments()


@app.get("/testing/chaos/evaluate")
def evaluate_testing_chaos_safety(experiment_id: str = "kill_api_pod"):
    return testing_dashboard_service.evaluate_chaos_safety(
        experiment_id=experiment_id,
    )


@app.get("/testing/chaos/validate")
def validate_testing_chaos():
    return testing_dashboard_service.validate_chaos_testing()


@app.get("/testing/contract/config")
def get_testing_contract_config():
    return testing_dashboard_service.get_contract_config()


@app.get("/testing/contract/contracts")
def list_testing_contracts():
    return testing_dashboard_service.list_contracts()


@app.get("/testing/contract/validate-change")
def validate_testing_contract_change(change_type: str = "add_optional_field"):
    return testing_dashboard_service.validate_contract_change(
        change_type=change_type,
    )


@app.get("/testing/contract/validate")
def validate_testing_contract():
    return testing_dashboard_service.validate_contract_testing()


@app.get("/testing/security/config")
def get_testing_security_config():
    return testing_dashboard_service.get_security_test_config()


@app.get("/testing/security/cases")
def list_testing_security_cases():
    return testing_dashboard_service.list_security_test_cases()


@app.get("/testing/security/run")
def run_testing_security_case(case_id: str = "jwt_expired"):
    return testing_dashboard_service.run_security_test_case(case_id=case_id)


@app.get("/testing/security/validate")
def validate_testing_security():
    return testing_dashboard_service.validate_security_testing()


@app.get("/testing/performance/config")
def get_testing_performance_config():
    return testing_dashboard_service.get_performance_test_config()


@app.get("/testing/performance/benchmarks")
def list_testing_performance_benchmarks():
    return testing_dashboard_service.list_performance_benchmarks()


@app.get("/testing/performance/evaluate")
def evaluate_testing_performance_benchmark(
    benchmark_id: str = "project_list",
    p95_ms: float = 0.0,
):
    return testing_dashboard_service.evaluate_performance_benchmark(
        benchmark_id=benchmark_id,
        p95_ms=p95_ms,
    )


@app.get("/testing/performance/validate")
def validate_testing_performance():
    return testing_dashboard_service.validate_performance_testing()


@app.get("/testing/regression/config")
def get_testing_regression_config():
    return testing_dashboard_service.get_regression_config()


@app.get("/testing/regression/suites")
def list_testing_regression_suites():
    return testing_dashboard_service.list_regression_suites()


@app.get("/testing/regression/compare")
def compare_testing_regression_baseline(
    suite_id: str = "api_responses",
    changed_snapshots: int = 0,
):
    return testing_dashboard_service.compare_regression_baseline(
        suite_id=suite_id,
        changed_snapshots=changed_snapshots,
    )


@app.get("/testing/regression/validate")
def validate_testing_regression():
    return testing_dashboard_service.validate_regression_testing()


# ==========================================
# PRODUCT READINESS
# ==========================================


@app.get("/product-readiness/dashboard")
def get_product_readiness_dashboard():
    return product_readiness_dashboard_service.get_dashboard()


@app.get("/product-readiness/onboarding/config")
def get_product_onboarding_config():
    return product_readiness_dashboard_service.get_onboarding_config()


@app.get("/product-readiness/onboarding/steps")
def list_product_onboarding_steps():
    return product_readiness_dashboard_service.list_onboarding_steps()


@app.get("/product-readiness/onboarding/progress")
def evaluate_product_onboarding_progress(completed_steps: str = ""):
    return product_readiness_dashboard_service.evaluate_onboarding_progress(
        completed_steps=completed_steps,
    )


@app.get("/product-readiness/onboarding/validate")
def validate_product_onboarding_flow():
    return product_readiness_dashboard_service.validate_onboarding_flow()


@app.get("/product-readiness/demo-data/config")
def get_product_demo_data_config():
    return product_readiness_dashboard_service.get_demo_data_config()


@app.get("/product-readiness/demo-data/presets")
def list_product_demo_data_presets():
    return product_readiness_dashboard_service.list_demo_data_presets()


@app.get("/product-readiness/demo-data/simulate")
def simulate_product_demo_data(preset_id: str = "startup"):
    return product_readiness_dashboard_service.simulate_demo_data(preset_id=preset_id)


@app.get("/product-readiness/demo-data/validate")
def validate_product_demo_data_generator():
    return product_readiness_dashboard_service.validate_demo_data_generator()


@app.get("/product-readiness/multi-tenant/config")
def get_product_multi_tenant_config():
    return product_readiness_dashboard_service.get_multi_tenant_config()


@app.get("/product-readiness/multi-tenant/checklist")
def list_product_multi_tenant_checklist():
    return product_readiness_dashboard_service.list_multi_tenant_checklist()


@app.get("/product-readiness/multi-tenant/evaluate")
def evaluate_product_multi_tenant_readiness(passed_items: str = ""):
    return product_readiness_dashboard_service.evaluate_multi_tenant_readiness(
        passed_items=passed_items,
    )


@app.get("/product-readiness/multi-tenant/validate")
def validate_product_multi_tenant_readiness():
    return product_readiness_dashboard_service.validate_multi_tenant_readiness()


@app.get("/product-readiness/pricing/config")
def get_product_pricing_config():
    return product_readiness_dashboard_service.get_pricing_config()


@app.get("/product-readiness/pricing/tiers")
def list_product_pricing_tiers():
    return product_readiness_dashboard_service.list_pricing_tiers()


@app.get("/product-readiness/pricing/estimate")
def calculate_product_pricing_estimate(
    tier_id: str = "starter",
    seats: int = 5,
    billing_period: str = "monthly",
):
    return product_readiness_dashboard_service.calculate_pricing_estimate(
        tier_id=tier_id,
        seats=seats,
        billing_period=billing_period,
    )


@app.get("/product-readiness/pricing/validate")
def validate_product_pricing_model():
    return product_readiness_dashboard_service.validate_pricing_model()


@app.get("/product-readiness/admin/config")
def get_product_admin_panel_config():
    return product_readiness_dashboard_service.get_admin_panel_config()


@app.get("/product-readiness/admin/modules")
def list_product_admin_modules():
    return product_readiness_dashboard_service.list_admin_modules()


@app.get("/product-readiness/admin/access")
def check_product_admin_access(role: str = "VIEWER"):
    return product_readiness_dashboard_service.check_admin_access(role=role)


@app.get("/product-readiness/admin/validate")
def validate_product_admin_panel():
    return product_readiness_dashboard_service.validate_admin_panel()


@app.get("/product-readiness/analytics/config")
def get_product_analytics_config():
    return product_readiness_dashboard_service.get_product_analytics_config()


@app.get("/product-readiness/analytics/events")
def list_product_analytics_events():
    return product_readiness_dashboard_service.list_product_analytics_events()


@app.get("/product-readiness/analytics/evaluate")
def evaluate_product_analytics(events_implemented: str = ""):
    return product_readiness_dashboard_service.evaluate_product_analytics(
        events_implemented=events_implemented,
    )


@app.get("/product-readiness/analytics/validate")
def validate_product_analytics():
    return product_readiness_dashboard_service.validate_product_analytics()


@app.get("/product-readiness/quotas/config")
def get_product_usage_quotas_config():
    return product_readiness_dashboard_service.get_usage_quotas_config()


@app.get("/product-readiness/quotas/list")
def list_product_usage_quotas():
    return product_readiness_dashboard_service.list_usage_quotas()


@app.get("/product-readiness/quotas/check")
def check_product_usage_quota(
    metric: str = "ai_tokens",
    plan: str = "starter",
    current_usage: int = 0,
):
    return product_readiness_dashboard_service.check_usage_quota(
        metric=metric,
        plan=plan,
        current_usage=current_usage,
    )


@app.get("/product-readiness/quotas/validate")
def validate_product_usage_quotas():
    return product_readiness_dashboard_service.validate_usage_quotas()


@app.get("/product-readiness/billing/config")
def get_product_billing_config():
    return product_readiness_dashboard_service.get_billing_config()


@app.get("/product-readiness/billing/products")
def list_product_billing_products():
    return product_readiness_dashboard_service.list_billing_products()


@app.get("/product-readiness/billing/webhook")
def simulate_product_billing_webhook(event_type: str = "invoice.paid"):
    return product_readiness_dashboard_service.simulate_billing_webhook(
        event_type=event_type,
    )


@app.get("/product-readiness/billing/validate")
def validate_product_billing_integration():
    return product_readiness_dashboard_service.validate_billing_integration()


@app.get("/product-readiness/subscriptions/config")
def get_product_subscription_config():
    return product_readiness_dashboard_service.get_subscription_config()


@app.get("/product-readiness/subscriptions/plans")
def list_product_subscription_plans():
    return product_readiness_dashboard_service.list_subscription_plans()


@app.get("/product-readiness/subscriptions/upgrade")
def evaluate_product_subscription_upgrade(
    from_plan: str = "starter",
    to_plan: str = "growth",
):
    return product_readiness_dashboard_service.evaluate_subscription_upgrade(
        from_plan=from_plan,
        to_plan=to_plan,
    )


@app.get("/product-readiness/subscriptions/validate")
def validate_product_subscription_plans():
    return product_readiness_dashboard_service.validate_subscription_plans()


@app.get("/product-readiness/support/config")
def get_product_support_config():
    return product_readiness_dashboard_service.get_support_config()


@app.get("/product-readiness/support/channels")
def list_product_support_channels():
    return product_readiness_dashboard_service.list_support_channels()


@app.get("/product-readiness/support/sla")
def evaluate_product_support_sla(
    plan: str = "starter",
    hours_open: float = 0.0,
):
    return product_readiness_dashboard_service.evaluate_support_sla(
        plan=plan,
        hours_open=hours_open,
    )


@app.get("/product-readiness/support/validate")
def validate_product_support_tooling():
    return product_readiness_dashboard_service.validate_support_tooling()


@app.get("/product-readiness/documentation/config")
def get_product_documentation_config():
    return product_readiness_dashboard_service.get_documentation_config()


@app.get("/product-readiness/documentation/sections")
def list_product_documentation_sections():
    return product_readiness_dashboard_service.list_documentation_sections()


@app.get("/product-readiness/documentation/coverage")
def evaluate_product_documentation_coverage(published_sections: str = ""):
    return product_readiness_dashboard_service.evaluate_documentation_coverage(
        published_sections=published_sections,
    )


@app.get("/product-readiness/documentation/validate")
def validate_product_documentation():
    return product_readiness_dashboard_service.validate_documentation()


@app.get("/product-readiness/api-docs/config")
def get_product_api_docs_config():
    return product_readiness_dashboard_service.get_api_docs_config()


@app.get("/product-readiness/api-docs/groups")
def list_product_api_doc_groups():
    return product_readiness_dashboard_service.list_api_doc_groups()


@app.get("/product-readiness/api-docs/completeness")
def evaluate_product_api_docs_completeness(documented_tags: str = ""):
    return product_readiness_dashboard_service.evaluate_api_docs_completeness(
        documented_tags=documented_tags,
    )


@app.get("/product-readiness/api-docs/validate")
def validate_product_api_documentation():
    return product_readiness_dashboard_service.validate_api_documentation()


@app.get("/product-readiness/dev-docs/config")
def get_product_internal_docs_config():
    return product_readiness_dashboard_service.get_internal_docs_config()


@app.get("/product-readiness/dev-docs/guides")
def list_product_internal_docs_guides():
    return product_readiness_dashboard_service.list_internal_docs_guides()


@app.get("/product-readiness/dev-docs/onboarding")
def evaluate_product_internal_docs_onboarding(available_guides: str = ""):
    return product_readiness_dashboard_service.evaluate_internal_docs_onboarding(
        available_guides=available_guides,
    )


@app.get("/product-readiness/dev-docs/validate")
def validate_product_internal_developer_docs():
    return product_readiness_dashboard_service.validate_internal_developer_docs()


@app.get("/product-readiness/website/config")
def get_product_website_config():
    return product_readiness_dashboard_service.get_product_website_config()


@app.get("/product-readiness/website/pages")
def list_product_website_pages():
    return product_readiness_dashboard_service.list_product_website_pages()


@app.get("/product-readiness/website/launch")
def evaluate_product_website_launch(published_slugs: str = ""):
    return product_readiness_dashboard_service.evaluate_product_website_launch(
        published_slugs=published_slugs,
    )


@app.get("/product-readiness/website/validate")
def validate_product_website():
    return product_readiness_dashboard_service.validate_product_website()


@app.get("/product-readiness/marketing/config")
def get_product_marketing_assets_config():
    return product_readiness_dashboard_service.get_marketing_assets_config()


@app.get("/product-readiness/marketing/assets")
def list_product_marketing_assets():
    return product_readiness_dashboard_service.list_marketing_assets()


@app.get("/product-readiness/marketing/check")
def check_product_marketing_asset(asset_id: str = "logo_primary"):
    return product_readiness_dashboard_service.check_marketing_asset(asset_id=asset_id)


@app.get("/product-readiness/marketing/validate")
def validate_product_marketing_assets():
    return product_readiness_dashboard_service.validate_marketing_assets()


@app.get("/product-readiness/investor-deck/config")
def get_product_investor_deck_config():
    return product_readiness_dashboard_service.get_investor_deck_config()


@app.get("/product-readiness/investor-deck/slides")
def list_product_investor_deck_slides():
    return product_readiness_dashboard_service.list_investor_deck_slides()


@app.get("/product-readiness/investor-deck/evaluate")
def evaluate_product_investor_deck(completed_slides: str = ""):
    return product_readiness_dashboard_service.evaluate_investor_deck(
        completed_slides=completed_slides,
    )


@app.get("/product-readiness/investor-deck/validate")
def validate_product_investor_demo_deck():
    return product_readiness_dashboard_service.validate_investor_demo_deck()


@app.get("/product-readiness/demo-env/config")
def get_product_demo_environment_config():
    return product_readiness_dashboard_service.get_demo_environment_config()


@app.get("/product-readiness/demo-env/features")
def list_product_demo_environment_features():
    return product_readiness_dashboard_service.list_demo_environment_features()


@app.get("/product-readiness/demo-env/health")
def evaluate_product_demo_environment_health(
    api_up: bool = True,
    ui_up: bool = True,
    data_seeded: bool = True,
):
    return product_readiness_dashboard_service.evaluate_demo_environment_health(
        api_up=api_up,
        ui_up=ui_up,
        data_seeded=data_seeded,
    )


@app.get("/product-readiness/demo-env/validate")
def validate_product_demo_environment():
    return product_readiness_dashboard_service.validate_demo_environment()


@app.get("/product-readiness/beta/config")
def get_product_beta_testing_config():
    return product_readiness_dashboard_service.get_beta_testing_config()


@app.get("/product-readiness/beta/stages")
def list_product_beta_testing_stages():
    return product_readiness_dashboard_service.list_beta_testing_stages()


@app.get("/product-readiness/beta/enrollment")
def evaluate_product_beta_enrollment(
    current_participants: int = 0,
    approved: bool = True,
):
    return product_readiness_dashboard_service.evaluate_beta_enrollment(
        current_participants=current_participants,
        approved=approved,
    )


@app.get("/product-readiness/beta/validate")
def validate_product_beta_testing_flow():
    return product_readiness_dashboard_service.validate_beta_testing_flow()


@app.get("/product-readiness/customer-onboarding/config")
def get_product_customer_onboarding_config():
    return product_readiness_dashboard_service.get_customer_onboarding_config()


@app.get("/product-readiness/customer-onboarding/milestones")
def list_product_customer_onboarding_milestones():
    return product_readiness_dashboard_service.list_customer_onboarding_milestones()


@app.get("/product-readiness/customer-onboarding/progress")
def evaluate_product_customer_onboarding(completed_milestones: str = ""):
    return product_readiness_dashboard_service.evaluate_customer_onboarding(
        completed_milestones=completed_milestones,
    )


@app.get("/product-readiness/customer-onboarding/validate")
def validate_product_customer_onboarding_flow():
    return product_readiness_dashboard_service.validate_customer_onboarding_flow()


@app.get("/product-readiness/saas/config")
def get_product_saas_readiness_config():
    return product_readiness_dashboard_service.get_saas_readiness_config()


@app.get("/product-readiness/saas/categories")
def list_product_saas_readiness_categories():
    return product_readiness_dashboard_service.list_saas_readiness_categories()


@app.get("/product-readiness/saas/assessment")
def run_product_saas_readiness_assessment(passed_checks: str | None = None):
    return product_readiness_dashboard_service.run_saas_readiness_assessment(
        passed_checks=passed_checks,
    )


@app.get("/product-readiness/saas/validate")
def validate_product_saas_readiness():
    return product_readiness_dashboard_service.validate_saas_readiness()


@app.get("/product-readiness/usage-tracking/config")
def get_product_usage_tracking_config():
    return product_readiness_dashboard_service.get_usage_tracking_config()


@app.get("/product-readiness/usage-tracking/metrics")
def list_product_usage_tracking_metrics():
    return product_readiness_dashboard_service.list_usage_tracking_metrics()


@app.get("/product-readiness/usage-tracking/record")
def record_product_usage(
    organization_id: str = "org-1",
    metric: str = "ai_tokens",
    amount: int = 0,
):
    return product_readiness_dashboard_service.track_usage(
        organization_id=organization_id,
        metric=metric,
        amount=amount,
    )


@app.get("/product-readiness/usage-tracking/summary")
def summarize_product_usage(
    organization_id: str = "org-1",
    ai_tokens: int = 0,
    reports: int = 0,
    api_requests: int = 0,
    storage_gb: int = 0,
    active_users: int = 0,
):
    return product_readiness_dashboard_service.summarize_usage_tracking(
        organization_id=organization_id,
        ai_tokens=ai_tokens,
        reports=reports,
        api_requests=api_requests,
        storage_gb=storage_gb,
        active_users=active_users,
    )


@app.get("/product-readiness/usage-tracking/validate")
def validate_product_usage_tracking():
    return product_readiness_dashboard_service.validate_usage_tracking()


@app.get("/product-readiness/product-demo/config")
def get_product_demo_config():
    return product_readiness_dashboard_service.get_product_demo_config()


@app.get("/product-readiness/product-demo/scenarios")
def list_product_demo_scenarios():
    return product_readiness_dashboard_service.list_product_demo_scenarios()


@app.get("/product-readiness/product-demo/evaluate")
def evaluate_product_demo(completed_scenarios: str = ""):
    return product_readiness_dashboard_service.evaluate_product_demo(
        completed_scenarios=completed_scenarios,
    )


@app.get("/product-readiness/product-demo/validate")
def validate_product_demo():
    return product_readiness_dashboard_service.validate_product_demo()

# ==========================================
# FUTURE AI FEATURES
# ==========================================


@app.get("/future-ai/dashboard")
def get_future_ai_dashboard():
    return future_ai_features_dashboard_service.get_dashboard()

@app.get("/future-ai/autonomous-workflows/config")
def future_ai_autonomous_workflows_config():
    return future_ai_features_dashboard_service.get_autonomous_workflows_config()

@app.get("/future-ai/autonomous-workflows/templates")
def future_ai_autonomous_workflows_templates():
    return future_ai_features_dashboard_service.list_autonomous_workflow_templates()

@app.get("/future-ai/autonomous-workflows/run")
def future_ai_autonomous_workflows_run(template_id: str = "escalation_response", approved: bool = True):
    return future_ai_features_dashboard_service.evaluate_autonomous_workflow_run(template_id=template_id, approved=approved)

@app.get("/future-ai/autonomous-workflows/validate")
def future_ai_autonomous_workflows_validate():
    return future_ai_features_dashboard_service.validate_autonomous_workflows()

@app.get("/future-ai/ai-action-generation/config")
def future_ai_ai_action_generation_config():
    return future_ai_features_dashboard_service.get_ai_action_generation_config()

@app.get("/future-ai/ai-action-generation/types")
def future_ai_ai_action_generation_types():
    return future_ai_features_dashboard_service.list_ai_action_generation_types()

@app.get("/future-ai/ai-action-generation/simulate")
def future_ai_ai_action_generation_simulate(project_id: str = "p1", signal_count: int = 3):
    return future_ai_features_dashboard_service.simulate_ai_action_generation(project_id=project_id, signal_count=signal_count)

@app.get("/future-ai/ai-action-generation/validate")
def future_ai_ai_action_generation_validate():
    return future_ai_features_dashboard_service.validate_ai_action_generation()

@app.get("/future-ai/project-forecasting/config")
def future_ai_project_forecasting_config():
    return future_ai_features_dashboard_service.get_ai_project_forecasting_config()

@app.get("/future-ai/project-forecasting/metrics")
def future_ai_project_forecasting_metrics():
    return future_ai_features_dashboard_service.list_ai_project_forecast_metrics()

@app.get("/future-ai/project-forecasting/forecast")
def future_ai_project_forecasting_forecast(project_id: str = "p1", health_score: int = 55):
    return future_ai_features_dashboard_service.run_ai_project_forecast(project_id=project_id, health_score=health_score)

@app.get("/future-ai/project-forecasting/validate")
def future_ai_project_forecasting_validate():
    return future_ai_features_dashboard_service.validate_ai_project_forecasting()

@app.get("/future-ai/anomaly-detection/config")
def future_ai_anomaly_detection_config():
    return future_ai_features_dashboard_service.get_ai_anomaly_detection_config()

@app.get("/future-ai/anomaly-detection/detectors")
def future_ai_anomaly_detection_detectors():
    return future_ai_features_dashboard_service.list_ai_anomaly_detectors()

@app.get("/future-ai/anomaly-detection/scan")
def future_ai_anomaly_detection_scan(metric: str = "actions", current_value: float = 120.0, baseline: float = 40.0):
    return future_ai_features_dashboard_service.scan_ai_anomalies(metric=metric, current_value=current_value, baseline=baseline)

@app.get("/future-ai/anomaly-detection/validate")
def future_ai_anomaly_detection_validate():
    return future_ai_features_dashboard_service.validate_ai_anomaly_detection()

@app.get("/future-ai/scheduling-optimization/config")
def future_ai_scheduling_optimization_config():
    return future_ai_features_dashboard_service.get_ai_scheduling_optimization_config()

@app.get("/future-ai/scheduling-optimization/constraints")
def future_ai_scheduling_optimization_constraints():
    return future_ai_features_dashboard_service.list_ai_scheduling_constraints()

@app.get("/future-ai/scheduling-optimization/optimize")
def future_ai_scheduling_optimization_optimize(action_count: int = 8, available_hours: float = 6.0):
    return future_ai_features_dashboard_service.run_ai_schedule_optimization(action_count=action_count, available_hours=available_hours)

@app.get("/future-ai/scheduling-optimization/validate")
def future_ai_scheduling_optimization_validate():
    return future_ai_features_dashboard_service.validate_ai_scheduling_optimization()

@app.get("/future-ai/recommendation-engine/config")
def future_ai_recommendation_engine_config():
    return future_ai_features_dashboard_service.get_ai_recommendation_engine_config()

@app.get("/future-ai/recommendation-engine/types")
def future_ai_recommendation_engine_types():
    return future_ai_features_dashboard_service.list_ai_recommendation_types()

@app.get("/future-ai/recommendation-engine/generate")
def future_ai_recommendation_engine_generate(context: str = "project", item_count: int = 3):
    return future_ai_features_dashboard_service.generate_ai_recommendations(context=context, item_count=item_count)

@app.get("/future-ai/recommendation-engine/validate")
def future_ai_recommendation_engine_validate():
    return future_ai_features_dashboard_service.validate_ai_recommendation_engine()

@app.get("/future-ai/executive-assistant/config")
def future_ai_executive_assistant_config():
    return future_ai_features_dashboard_service.get_ai_executive_assistant_config()

@app.get("/future-ai/executive-assistant/capabilities")
def future_ai_executive_assistant_capabilities():
    return future_ai_features_dashboard_service.list_ai_executive_assistant_capabilities()

@app.get("/future-ai/executive-assistant/briefing")
def future_ai_executive_assistant_briefing(topics: str = ""):
    return future_ai_features_dashboard_service.compose_ai_executive_briefing(topics=topics)

@app.get("/future-ai/executive-assistant/validate")
def future_ai_executive_assistant_validate():
    return future_ai_features_dashboard_service.validate_ai_executive_assistant()

@app.get("/future-ai/voice-summaries/config")
def future_ai_voice_summaries_config():
    return future_ai_features_dashboard_service.get_voice_summaries_config()

@app.get("/future-ai/voice-summaries/voices")
def future_ai_voice_summaries_voices():
    return future_ai_features_dashboard_service.list_voice_summary_voices()

@app.get("/future-ai/voice-summaries/synthesize")
def future_ai_voice_summaries_synthesize(text_length: int = 500):
    return future_ai_features_dashboard_service.synthesize_voice_summary(text_length=text_length)

@app.get("/future-ai/voice-summaries/validate")
def future_ai_voice_summaries_validate():
    return future_ai_features_dashboard_service.validate_voice_summaries()

@app.get("/future-ai/whatsapp/config")
def future_ai_whatsapp_config():
    return future_ai_features_dashboard_service.get_whatsapp_integration_config()

@app.get("/future-ai/whatsapp/templates")
def future_ai_whatsapp_templates():
    return future_ai_features_dashboard_service.list_whatsapp_templates()

@app.get("/future-ai/whatsapp/webhook")
def future_ai_whatsapp_webhook(signature_valid: bool = True):
    return future_ai_features_dashboard_service.validate_whatsapp_webhook(signature_valid=signature_valid)

@app.get("/future-ai/whatsapp/validate")
def future_ai_whatsapp_validate():
    return future_ai_features_dashboard_service.validate_whatsapp_integration()

@app.get("/future-ai/email-ingestion/config")
def future_ai_email_ingestion_config():
    return future_ai_features_dashboard_service.get_email_ingestion_ai_config()

@app.get("/future-ai/email-ingestion/parsers")
def future_ai_email_ingestion_parsers():
    return future_ai_features_dashboard_service.list_email_ingestion_parsers()

@app.get("/future-ai/email-ingestion/process")
def future_ai_email_ingestion_process(has_attachment: bool = True, subject: str = "Q1 report"):
    return future_ai_features_dashboard_service.process_email_ingestion(has_attachment=has_attachment, subject=subject)

@app.get("/future-ai/email-ingestion/validate")
def future_ai_email_ingestion_validate():
    return future_ai_features_dashboard_service.validate_email_ingestion_ai()

@app.get("/future-ai/sharepoint/config")
def future_ai_sharepoint_config():
    return future_ai_features_dashboard_service.get_sharepoint_integration_config()

@app.get("/future-ai/sharepoint/targets")
def future_ai_sharepoint_targets():
    return future_ai_features_dashboard_service.list_sharepoint_sync_targets()

@app.get("/future-ai/sharepoint/sync")
def future_ai_sharepoint_sync(site_id: str = "site-1", files_found: int = 5):
    return future_ai_features_dashboard_service.sync_sharepoint_library(site_id=site_id, files_found=files_found)

@app.get("/future-ai/sharepoint/validate")
def future_ai_sharepoint_validate():
    return future_ai_features_dashboard_service.validate_sharepoint_integration()

@app.get("/future-ai/teams/config")
def future_ai_teams_config():
    return future_ai_features_dashboard_service.get_teams_integration_config()

@app.get("/future-ai/teams/commands")
def future_ai_teams_commands():
    return future_ai_features_dashboard_service.list_teams_commands()

@app.get("/future-ai/teams/notify")
def future_ai_teams_notify(channel_id: str = "general", urgent: bool = False):
    return future_ai_features_dashboard_service.post_teams_notification(channel_id=channel_id, urgent=urgent)

@app.get("/future-ai/teams/validate")
def future_ai_teams_validate():
    return future_ai_features_dashboard_service.validate_teams_integration()

@app.get("/future-ai/slack/config")
def future_ai_slack_config():
    return future_ai_features_dashboard_service.get_slack_integration_config()

@app.get("/future-ai/slack/commands")
def future_ai_slack_commands():
    return future_ai_features_dashboard_service.list_slack_slash_commands()

@app.get("/future-ai/slack/events")
def future_ai_slack_events(event_type: str = "app_mention"):
    return future_ai_features_dashboard_service.handle_slack_event(event_type=event_type)

@app.get("/future-ai/slack/validate")
def future_ai_slack_validate():
    return future_ai_features_dashboard_service.validate_slack_integration()

@app.get("/future-ai/copilots/config")
def future_ai_copilots_config():
    return future_ai_features_dashboard_service.get_ai_copilots_config()

@app.get("/future-ai/copilots/list")
def future_ai_copilots_list():
    return future_ai_features_dashboard_service.list_ai_copilots()

@app.get("/future-ai/copilots/invoke")
def future_ai_copilots_invoke(copilot_id: str = "project_copilot", prompt_length: int = 50):
    return future_ai_features_dashboard_service.invoke_ai_copilot(copilot_id=copilot_id, prompt_length=prompt_length)

@app.get("/future-ai/copilots/validate")
def future_ai_copilots_validate():
    return future_ai_features_dashboard_service.validate_ai_copilots()

@app.get("/future-ai/conversational-workspace/config")
def future_ai_conversational_workspace_config():
    return future_ai_features_dashboard_service.get_conversational_workspace_ai_config()

@app.get("/future-ai/conversational-workspace/tools")
def future_ai_conversational_workspace_tools():
    return future_ai_features_dashboard_service.list_conversational_workspace_tools()

@app.get("/future-ai/conversational-workspace/chat")
def future_ai_conversational_workspace_chat(message: str = "Summarize today", project_id: str = "p1"):
    return future_ai_features_dashboard_service.chat_conversational_workspace(message=message, project_id=project_id)

@app.get("/future-ai/conversational-workspace/validate")
def future_ai_conversational_workspace_validate():
    return future_ai_features_dashboard_service.validate_conversational_workspace_ai()

@app.get("/future-ai/recovery-agents/config")
def future_ai_recovery_agents_config():
    return future_ai_features_dashboard_service.get_autonomous_recovery_agents_config()

@app.get("/future-ai/recovery-agents/agents")
def future_ai_recovery_agents_agents():
    return future_ai_features_dashboard_service.list_autonomous_recovery_agents()

@app.get("/future-ai/recovery-agents/triage")
def future_ai_recovery_agents_triage(failure_category: str = "transient", retry_count: int = 1):
    return future_ai_features_dashboard_service.triage_autonomous_recovery_failure(failure_category=failure_category, retry_count=retry_count)

@app.get("/future-ai/recovery-agents/validate")
def future_ai_recovery_agents_validate():
    return future_ai_features_dashboard_service.validate_autonomous_recovery_agents()
