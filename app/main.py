from fastapi import FastAPI
from pydantic import BaseModel

from app.agent.orchestrator import Orchestrator


app = FastAPI(title="OrgFlow Agent")


class AgentRunRequest(BaseModel):
    user_request: str


class ConfirmRequest(BaseModel):
    run_id: str


orchestrator = Orchestrator()

@app.get("/")
def root():
    return {
        "message": "OrgFlow Agent is running",
        "docs": "http://127.0.0.1:8000/docs"
    }

@app.get("/health")
def health_check():
    return {
        "status": "OK",
        "service": "OrgFlow Agent"
    }

@app.post("/agent/run")
def run_agent(request: AgentRunRequest):
    return orchestrator.run(request.user_request)

@app.post("/agent/confirm")
def confirm_workflow(request: ConfirmRequest):
    return orchestrator.confirm(request.run_id)

@app.get("/workflow-runs")
def get_workflow_runs():
    return orchestrator.get_history()