from datetime import datetime

from pydantic import BaseModel


class ActionComment(
    BaseModel
):

    action_id: str

    comment: str

    created_by: str

    created_at:
        datetime | None = None