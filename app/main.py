import os
import shutil

from pathlib import Path

from dotenv import load_dotenv

from fastapi import (
    FastAPI,
    HTTPException,
    UploadFile,
    File,
    Form,
)

from fastapi.middleware.cors import (
    CORSMiddleware
)

from pydantic import BaseModel

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

# ==========================================
# ENV
# ==========================================

load_dotenv()

FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://localhost:3000"
)

FRONTEND_URLS = [
    FRONTEND_URL,
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# ==========================================
# APP
# ==========================================

app = FastAPI()

DEMO_ORGANIZATION_ID = (
    "bb2c760b-81cb-4e49-b057-4426406d5e71"
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

# ==========================================
# AUTOMATION ENGINE
# ==========================================

register_automation_jobs()

scheduler.start()

print(
    "[AUTOMATION] Scheduler started"
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


# ==========================================
# ROOT
# ==========================================

@app.get("/")
def root():

    return {
        "message":
            "OrgFlow AI Agent is running"
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
def get_profile_notifications(profile_id: str):

    return (
        notification_service
        .get_notifications(profile_id)
    )

@app.get("/projects/{project_id}/workspace")
def get_project_workspace(project_id: str):

    return (
        project_workspace_service
        .get_workspace(project_id)
    )

@app.get("/projects/{project_id}/exceptions")
def get_project_exceptions(project_id: str):

    return (
        operational_action_repository
        .get_exceptions_by_project(project_id)
    )

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


@app.get(
    "/automation/ai-recovery"
)
def get_automation_ai_recovery():

    return (
        automation_monitoring_service
        .get_ai_recovery_monitoring()
    )


@app.get(
    "/automation/ai-execution-logs"
)
def get_automation_ai_execution_logs():

    return (
        automation_monitoring_service
        .get_ai_execution_logs_dashboard()
    )
