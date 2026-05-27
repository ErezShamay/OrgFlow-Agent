from datetime import datetime

from pydantic import BaseModel


class AutomationLock(
    BaseModel
):

    id: str

    lock_key: str

    created_at: datetime

    expires_at: datetime