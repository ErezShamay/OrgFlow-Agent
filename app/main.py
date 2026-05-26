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

    project = (
        project_repository
        .get_project_by_id(
            project_id
        )
    )

    reviews = (
        ai_review_service
        .get_reviews_by_project(
            project_id
        )
    )

    actions = (
        operational_action_repository
        .get_open_actions_by_project(
            project_id
        )
    )

    exceptions = (
        operational_action_repository
        .get_exceptions_by_project(
            project_id
        )
    )

    activities = (
        WorkspaceActivityRepository
        .get_project_activity(
            project_id
        )
    )

    insights = (
        ProjectInsightsService
        .generate_project_insights(
            project_id
        )
    )

    reports = (
        weekly_report_repository
        .get_reports_by_project(
            project_id
        )
    )

    summary = {

        "reviews_count":
            len(reviews),

        "actions_count":
            len(actions),

        "escalations_count":
            len(exceptions),

        "reports_count":
            len(reports),
    }

    return {
        "project": project,
        "reviews": reviews,
        "actions": actions,
        "exceptions": exceptions,
        "activities": activities,
        "insights": insights,
        "summary": summary,
    }

# ==========================================
# ORGANIZATION APIs
# ==========================================

@app.get("/organizations")
def get_organizations():

    return (
        organization_repository
        .get_all_organizations()
    )