from fastapi import FastAPI
from pydantic import BaseModel

from app.agent.orchestrator import Orchestrator
from app.agent.workflow_history import (
    WorkflowHistory
)
from app.services.approval_service import (
    ApprovalService
)

app = FastAPI()

orchestrator = Orchestrator()
workflow_history = WorkflowHistory()
approval_service = ApprovalService()


class AgentRequest(BaseModel):
    user_request: str


@app.get("/")
def root():
    return {
        "message": "OrgFlow AI Agent is running"
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


@app.post("/approval/{approval_id}/approve")
def approve_request(
    approval_id: int
):
    return approval_service.approve(
        approval_id
    )


@app.get("/approval/{approval_id}")
def get_approval_request(
    approval_id: int
):
    return approval_service.get_request(
        approval_id
    )