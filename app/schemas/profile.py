from datetime import datetime

from pydantic import BaseModel


class Profile(
    BaseModel
):

    id: str

    email: str

    full_name:
        str | None = None

    role: str

    created_at:
        datetime | None = None