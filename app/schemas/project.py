from datetime import datetime
from typing import Literal

from pydantic import BaseModel

ProjectScheme = Literal[
    "TAMA38_STRENGTHENING",
    "TAMA38_DEMOLITION_REBUILD",
    "TAMA38_RELOCATED_BUILD",
    "NEW_CONSTRUCTION",
]


class Project(BaseModel):

    project_name: str

    city: str | None = None

    project_type: str | None = None

    developer_name: str | None = None

    scheme: ProjectScheme | None = None

    status: str = "active"

    created_at: datetime | None = None