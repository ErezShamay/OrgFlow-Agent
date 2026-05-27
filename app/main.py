import os
import shutil

from pathlib import Path

from dotenv import load_dotenv

from fastapi import (
    FastAPI,
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

    allow_origins=[
        FRONTEND_URL
    ],

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