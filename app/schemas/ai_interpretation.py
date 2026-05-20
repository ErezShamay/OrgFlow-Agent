from datetime import datetime

from pydantic import BaseModel


class AIInterpretation(BaseModel):

    finding_id: str

    model_name: str

    business_impact: str

    tenant_risk: str

    recommended_action: str

    raw_response: str

    review_status: str = "PENDING"

    reviewed_by: str | None = None

    reviewed_at: datetime | None = None

    review_notes: str | None = None

    created_at: datetime | None = None