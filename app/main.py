from fastapi import FastAPI

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
        "http://localhost:3000"
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


class AgentRequest(
    BaseModel
):

    user_request: str


class ReviewDecisionRequest(
    BaseModel
):

    reviewed_by: str

    review_notes: str | None = None


@app.get("/")
def root():

    return {
        "message":
            "OrgFlow AI Agent is running"
    }


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


@app.get("/actions/escalations")
def get_escalations():

    return (
        operational_action_service
        .get_escalations()
    )

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
    "/projects/{project_id}/reviews"
)
def get_project_reviews(
    project_id: str
):

    return (
        ai_review_service
        .get_reviews_by_project(
            project_id
        )
    )

@app.get(
    "/projects/{project_id}/summary"
)
def get_project_summary(
    project_id: str
):

    reviews = (
        ai_interpretation_repository
        .get_reviews_by_project(
            project_id
        )
    )

    actions = (
        operational_action_repository
        .get_open_actions()
    )

    escalations = [
        action
        for action in actions
        if action["action_type"]
        == "ESCALATION"
    ]

    reports = (
        weekly_report_repository
        .get_reports_by_project(
            project_id
        )
    )

    return {
        "reviews_count":
            len(reviews),

        "actions_count":
            len(actions),

        "escalations_count":
            len(escalations),

        "reports_count":
            len(reports),
    }

# ==========================================
# Organizations APIs
# ==========================================

@app.get("/organizations")
def get_organizations():

    return (
        organization_repository
        .get_all_organizations()
    )