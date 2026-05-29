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
                log.model_dump(
                    mode="json",
                    exclude_none=True
                )
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
    # GET RECENT EXECUTIONS
    # ==========================================

    def get_recent_executions(
        self,
        limit: int = 20,
    ):

        response = (
            self.client
            .table(self.table_name)
            .select("*")
            .order(
                "created_at",
                desc=True
            )
            .limit(limit)
            .execute()
        )

        return response.data

    # ==========================================
    # GET DEAD LETTERS
    # ==========================================

    def get_dead_letters(
        self,
        limit: int = 20,
    ):

        response = (
            self.client
            .table(self.table_name)
            .select("*")
            .eq(
                "dead_lettered",
                True
            )
            .order(
                "created_at",
                desc=True
            )
            .limit(limit)
            .execute()
        )

        return response.data

    # ==========================================
    # GET BY ID
    # ==========================================

    def get_by_id(
        self,
        log_id: str,
    ):

        response = (
            self.client
            .table(self.table_name)
            .select("*")
            .eq(
                "id",
                log_id,
            )
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]

    # ==========================================
    # SEARCH DEAD LETTERS
    # ==========================================

    def search_dead_letters(
        self,
        execution_type: str | None = None,
        failure_type: str | None = None,
        severity: str | None = None,
        project_id: str | None = None,
        query: str | None = None,
        limit: int = 50,
    ):

        request = (
            self.client
            .table(self.table_name)
            .select("*")
            .eq(
                "dead_lettered",
                True,
            )
        )

        if execution_type:
            request = request.eq(
                "execution_type",
                execution_type,
            )

        if failure_type:
            request = request.eq(
                "failure_type",
                failure_type,
            )

        if severity:
            request = request.eq(
                "severity",
                severity,
            )

        if project_id:
            request = request.eq(
                "project_id",
                project_id,
            )

        response = (
            request
            .order(
                "created_at",
                desc=True,
            )
            .limit(limit)
            .execute()
        )

        results = response.data

        if query:
            needle = query.lower()
            results = [
                item
                for item in results
                if needle in str(item.get("id", "")).lower()
                or needle in str(item.get("execution_type", "")).lower()
                or needle in str(item.get("failure_type", "")).lower()
                or needle in str(item.get("project_id", "")).lower()
            ]

        return results

    # ==========================================
    # REQUEUE FROM DEAD LETTER
    # ==========================================

    def requeue_from_dead_letter(
        self,
        log_id: str,
    ):

        payload = {
            "status": "FAILED",
            "dead_lettered": False,
            "recovery_locked": False,
            "retry_count": 0,
            "next_retry_at": None,
        }

        response = (
            self.client
            .table(self.table_name)
            .update(payload)
            .eq(
                "id",
                log_id,
            )
            .execute()
        )

        if not response.data:
            raise LookupError(f"Execution log '{log_id}' not found")

        return response.data[0]

    # ==========================================
    # MARK MANUAL RECOVERED
    # ==========================================

    def mark_manual_recovered(
        self,
        log_id: str,
    ):

        payload = {
            "status": "RECOVERED",
            "dead_lettered": False,
            "recovery_locked": False,
            "next_retry_at": None,
            "last_retry_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        response = (
            self.client
            .table(self.table_name)
            .update(payload)
            .eq(
                "id",
                log_id,
            )
            .execute()
        )

        if not response.data:
            raise LookupError(f"Execution log '{log_id}' not found")

        return response.data[0]

    # ==========================================
    # UPDATE RETRY
    # ==========================================

    def update_retry(
        self,
        log_id: str,
        retry_count: int,
        next_retry_at: datetime,
    ):

        payload = {

            "retry_count":
                retry_count,

            "last_retry_at":
                datetime.now(
                    timezone.utc
                ).isoformat(),

            "next_retry_at":
                next_retry_at.isoformat()
        }

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

                "status":
                    "DEAD_LETTERED",

                "dead_lettered":
                    True,

                "recovery_locked":
                    False,

                "next_retry_at":
                    None,
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
            }) \
            .eq(
                "id",
                log_id
            ) \
            .execute()
