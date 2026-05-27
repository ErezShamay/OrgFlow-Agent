import os
import shutil

from pathlib import Path

from dotenv import load_dotenv

from fastapi import (FastAPI, UploadFile, File, Form,)

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

from app.jobs.scheduler import (
    start_scheduler
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

from app.services.action_comment_service import (
    ActionCommentService
)

from app.services.profile_service import (
    ProfileService
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

action_comment_service = (
    ActionCommentService()
)

profile_service = (
    ProfileService()
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


@app.post(
    "/reviews/{interpretation_id}/approve"
)
def approve_review(
    interpretation_id: str,
    request: ReviewDecisionRequest
):

    return (
        ai_review_service
        .approve_review(
            interpretation_id=
                interpretation_id,

            reviewed_by=
                request.reviewed_by,

            review_notes=
                request.review_notes
        )
    )


@app.post(
    "/reviews/{interpretation_id}/reject"
)
def reject_review(
    interpretation_id: str,
    request: ReviewDecisionRequest
):

    return (
        ai_review_service
        .reject_review(
            interpretation_id=
                interpretation_id,

            reviewed_by=
                request.reviewed_by,

            review_notes=
                request.review_notes
        )
    )

# ==========================================
# OPERATIONAL ACTION APIs
# ==========================================

@app.get("/actions/open")
def get_open_actions():

    return (
        operational_action_service
        .get_open_actions()
    )

@app.get(
    "/actions/{action_id}"
)
def get_action_details(
    action_id: str
):

    return (
        operational_action_service
        .get_action_details(
            action_id
        )
    )


@app.get(
    "/projects/{project_id}/actions"
)
def get_project_actions(
    project_id: str
):

    return (
        operational_action_repository
        .get_open_actions_by_project(
            project_id
        )
    )


@app.get("/actions/escalations")
def get_escalations():

    return (
        operational_action_service
        .get_escalations()
    )


@app.post(
    "/actions/{action_id}/close"
)
def close_action(
    action_id: str
):

    return (
        operational_action_repository
        .close_action(
            action_id
        )
    )


@app.post(
    "/actions/{action_id}/assign"
)
def assign_action(
    action_id: str,
    payload: AssignActionRequest
):

    result = (
        operational_action_repository
        .assign_action(
            action_id=action_id,
            assigned_to=payload.assigned_to,
        )
    )

    return result

@app.post(
    "/actions/{action_id}/start"
)
def start_action(
    action_id: str
):

    return (
        operational_action_service
        .start_action(
            action_id
        )
    )


@app.post(
    "/actions/{action_id}/block"
)
def block_action(
    action_id: str
):

    return (
        operational_action_service
        .block_action(
            action_id
        )
    )


@app.post(
    "/actions/{action_id}/complete"
)
def complete_action(
    action_id: str
):

    return (
        operational_action_service
        .complete_action(
            action_id
        )
    )


@app.post(
    "/actions/{action_id}/escalate"
)
def escalate_action(
    action_id: str
):

    return (
        operational_action_service
        .escalate_action(
            action_id
        )
    )

# ==========================================
# REPORT UPLOAD API
# ==========================================

@app.post("/reports/upload")
async def upload_report(
    project_id: str = Form(...),
    file: UploadFile = File(...),
):

    uploads_dir = Path(
        "uploads"
    )

    uploads_dir.mkdir(
        exist_ok=True
    )

    file_path = (
        uploads_dir / file.filename
    )

    with open(
        file_path,
        "wb"
    ) as buffer:

        shutil.copyfileobj(
            file.file,
            buffer
        )

    ReportProcessingService.process_uploaded_report(
    project_id=project_id,
    filename=file.filename,
    file_path=str(file_path),
)

    return {
        "success": True,

        "project_id":
            project_id,

        "filename":
            file.filename,

        "path":
            str(file_path),
    }

# ==========================================
# PROJECT APIs
# ==========================================

@app.get("/projects")
def get_projects():

    return (
        project_repository
        .get_projects_by_organization(
            DEMO_ORGANIZATION_ID
        )
    )


@app.get("/projects/{project_id}")
def get_project(
    project_id: str
):

    return (
        project_repository
        .get_project_by_id(
            project_id
        )
    )


@app.get(
    "/projects/{project_id}/workspace"
)
def get_project_workspace(
    project_id: str
):

    return (
        project_workspace_service
        .get_workspace(
            project_id
        )
    )

# ==========================================
# ORGANIZATION APIs
# ==========================================

@app.get("/organizations")
def get_organizations():

    return (
        organization_repository
        .get_all_organizations()
    )

# ==========================================
# OPERATIONS APIs
# ==========================================

@app.post(
    "/operations/run-escalations"
)
def run_escalations():

    return (
        action_escalation_service
        .escalate_overdue_actions()
    )

@app.get(
    "/projects/{project_id}/operational-summary"
)
def get_operational_summary(
    project_id: str
):

    return (
        operational_summary_service
        .generate_project_summary(
            project_id
        )
    )

@app.on_event(
    "startup"
)
async def startup_event():

    start_scheduler()

@app.get(
    "/portfolio/summary"
)
def get_portfolio_summary():

    return (
        portfolio_insights_service
        .generate_portfolio_summary()
    )

@app.get(
    "/alerts"
)
def get_alerts():

    return (
        alert_engine_service
        .generate_alerts()
    )

# ==========================================
# ACTION COMMENTS APIs
# ==========================================

@app.get(
    "/actions/{action_id}/comments"
)
def get_action_comments(
    action_id: str
):

    return (
        action_comment_service
        .get_comments_by_action(
            action_id
        )
    )


@app.post(
    "/actions/{action_id}/comments"
)
def create_action_comment(
    action_id: str,
    payload: dict,
):

    return (
        action_comment_service
        .create_comment(

            action_id=
                action_id,

            comment=
                payload["comment"],

            created_by=
                payload["created_by"],
        )
    )

# ==========================================
# PROFILE APIs
# ==========================================

@app.get(
    "/profiles/{profile_id}"
)
def get_profile(
    profile_id: str
):

    return (
        profile_service
        .get_profile(
            profile_id
        )
    )