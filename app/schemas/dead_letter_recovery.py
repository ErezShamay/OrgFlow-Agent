from pydantic import BaseModel, Field


class DeadLetterSearchRequest(BaseModel):
    execution_type: str | None = None
    failure_type: str | None = None
    severity: str | None = None
    project_id: str | None = None
    query: str | None = None
    limit: int = Field(default=50, ge=1, le=500)


class RecoveryActionRequest(BaseModel):
    initiated_by: str = "operator"


class FailureCategorizationRequest(BaseModel):
    error_message: str


class RecoveryOrchestrationRequest(BaseModel):
    initiated_by: str = "system"
    limit: int = Field(default=25, ge=1, le=100)
