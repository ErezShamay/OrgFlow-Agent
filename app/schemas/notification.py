from datetime import datetime

from pydantic import BaseModel


class Notification(
    BaseModel
):

    profile_id: str

    title: str

    message: str

    notification_type: str

    is_read: bool = False

    created_at: datetime | None = None
