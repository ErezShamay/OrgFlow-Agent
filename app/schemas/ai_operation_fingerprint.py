from datetime import datetime

from pydantic import BaseModel


class AIOperationFingerprint(
    BaseModel
):

    id: str

    fingerprint: str

    project_id: str

    operation_type: str

    created_at: datetime

    expires_at: datetime | None = None