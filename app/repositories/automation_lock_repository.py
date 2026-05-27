from datetime import (
    datetime,
    timezone,
)

from app.db.supabase_client import (
    supabase
)

from app.schemas.automation_lock import (
    AutomationLock
)


class AutomationLockRepository:

    def __init__(self):

        self.client = (
            supabase
        )

        self.table_name = (
            "automation_locks"
        )

    # ==========================================
    # GET LOCK
    # ==========================================

    def get_lock(
        self,
        lock_key: str,
    ):

        response = (
            self.client
            .table(self.table_name)
            .select("*")
            .eq(
                "lock_key",
                lock_key
            )
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]

    # ==========================================
    # CREATE LOCK
    # ==========================================

    def create_lock(
        self,
        lock: AutomationLock,
    ):

        response = (
            self.client
            .table(self.table_name)
            .insert(
                lock.model_dump(
                    mode="json"
                )
            )
            .execute()
        )

        return response.data[0]

    # ==========================================
    # DELETE LOCK
    # ==========================================

    def delete_lock(
        self,
        lock_key: str,
    ):

        self.client \
            .table(self.table_name) \
            .delete() \
            .eq(
                "lock_key",
                lock_key
            ) \
            .execute()

    # ==========================================
    # LOCK EXPIRED
    # ==========================================

    def is_lock_expired(
        self,
        lock: dict,
    ):

        expires_at = (
            datetime.fromisoformat(
                lock[
                    "expires_at"
                ].replace(
                    "Z",
                    "+00:00"
                )
            )
        )

        return (
            expires_at
            < datetime.now(
                timezone.utc
            )
        )
