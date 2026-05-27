from app.db.supabase_client import (
    supabase
)

from app.schemas.ai_execution_log import (
    AIExecutionLog
)

from datetime import (
    datetime,
    timezone,
)


class AIExecutionLogRepository:

    def __init__(self):

        self.client = (
            supabase
        )

        self.table_name = (
            "ai_execution_logs"
        )

    # ==========================================
    # CREATE LOG
    # ==========================================

    def create_log(
        self,
        log: AIExecutionLog,
    ):

        response = (
            self.client
            .table(self.table_name)
            .insert(
                log.model_dump()
            )
            .execute()
        )

        return response.data[0]

    # ==========================================
    # GET FAILED EXECUTIONS
    # ==========================================

    def get_failed_executions(
        self,
    ):

        now = (
            datetime.now(
                timezone.utc
            ).isoformat()
        )

        response = (
            self.client
            .table(self.table_name)
            .select("*")

            .eq(
                "status",
                "FAILED"
            )

            .eq(
                "dead_lettered",
                False
            )

            .eq(
                "recovery_locked",
                False
            )

            .lt(
                "retry_count",
                3
            )

            .or_(
                f"next_retry_at.is.null,"
                f"next_retry_at.lte.{now}"
            )

            .order(
                "created_at",
                desc=False
            )

            .execute()
        )

        return response.data

    # ==========================================
    # UPDATE RETRY
    # ==========================================

    def update_retry(
        self,
        log_id: str,
        retry_count: int,
        next_retry_at: datetime | None = None,
    ):

        payload = {

            "retry_count":
                retry_count,

            "last_retry_at":
                datetime.now(
                    timezone.utc
                ).isoformat(),
        }

        if next_retry_at:

            payload["next_retry_at"] = (
                next_retry_at.isoformat()
            )

        self.client \
            .table(self.table_name) \
            .update(payload) \
            .eq(
                "id",
                log_id
            ) \
            .execute()

    # ==========================================
    # MARK RECOVERED
    # ==========================================

    def mark_recovered(
        self,
        log_id: str,
    ):

        self.client \
            .table(self.table_name) \
            .update({

                "status":
                    "RECOVERED",

                "last_retry_at":
                    datetime.now(
                        timezone.utc
                    ).isoformat(),

                "next_retry_at":
                    None,
            }) \
            .eq(
                "id",
                log_id
            ) \
            .execute()

    # ==========================================
    # MARK DEAD LETTER
    # ==========================================

    def mark_dead_letter(
        self,
        log_id: str,
    ):

        self.client \
            .table(self.table_name) \
            .update({

                "dead_lettered":
                    True,

                "recovery_locked":
                    False,
            }) \
            .eq(
                "id",
                log_id
            ) \
            .execute()

    # ==========================================
    # LOCK RECOVERY
    # ==========================================

    def lock_recovery(
        self,
        log_id: str,
    ):

        self.client \
            .table(self.table_name) \
            .update({

                "recovery_locked":
                    True,

                "recovery_locked_at":
                    datetime.now(
                        timezone.utc
                    ).isoformat(),
            }) \
            .eq(
                "id",
                log_id
            ) \
            .execute()

    # ==========================================
    # UNLOCK RECOVERY
    # ==========================================

    def unlock_recovery(
        self,
        log_id: str,
    ):

        self.client \
            .table(self.table_name) \
            .update({

                "recovery_locked":
                    False,

                "recovery_locked_at":
                    None,
            }) \
            .eq(
                "id",
                log_id
            ) \
            .execute()
