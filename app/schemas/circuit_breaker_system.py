from pydantic import BaseModel, Field


class CircuitBreakerThresholdRequest(BaseModel):
    breaker_key: str
    failure_threshold: int = Field(default=5, ge=1, le=100)
    cooldown_minutes: int = Field(default=10, ge=1, le=1440)
    half_open_success_threshold: int = Field(default=2, ge=1, le=10)


class CircuitBreakerReopenRequest(BaseModel):
    initiated_by: str = "operator"
    force_closed: bool = False
