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

app = FastAPI()

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