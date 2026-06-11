from datetime import datetime

from pydantic import BaseModel, Field


class PromptUsageSummary(BaseModel):
    prompt_name: str
    total_calls: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0


class OrganizationAIUsageSummary(BaseModel):
    organization_id: str
    organization_name: str
    contact_email: str | None = None
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    cache_hits: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    last_activity_at: datetime | None = None
    usage_by_prompt: list[PromptUsageSummary] = Field(default_factory=list)


class PlatformAIUsageTotals(BaseModel):
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    cache_hits: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    active_organizations: int = 0


class PlatformAIUsageDashboard(BaseModel):
    period_days: int
    generated_at: datetime
    pricing_disclaimer: str
    totals: PlatformAIUsageTotals
    organizations: list[OrganizationAIUsageSummary]
