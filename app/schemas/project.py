from datetime import datetime

from pydantic import BaseModel


class Project(BaseModel):

    project_name: str

    city: str | None = None

    project_type: str | None = None

    developer_name: str | None = None

    status: str = "active"

    created_at: datetime | None = None