from app.db.supabase_client import (
    supabase
)


class AILogRepository:

    @staticmethod
    def create_log(
        log_data: dict
    ):

        supabase.table(
            "ai_logs"
        ).insert(
            log_data
        ).execute()