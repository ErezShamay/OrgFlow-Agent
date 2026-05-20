from datetime import datetime

from pydantic import BaseModel


class OperationalAction(BaseModel):

    interpretation_id: str

    action_type: str

    title: str

    description: str

    status: str = "OPEN"

    assigned_to: str | None = None

    due_date: datetime | None = None

    created_at: datetime | None = None