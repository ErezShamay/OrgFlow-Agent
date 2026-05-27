from app.db.supabase_client import (
    supabase
)

from app.schemas.ai_operation_fingerprint import (
    AIOperationFingerprint
)

from datetime import (
    datetime,
    timezone,
)


class AIOperationFingerprintRepository:

    def __init__(self):

        self.client = (
            supabase
        )

        self.table_name = (
            "ai_operation_fingerprints"
        )

    # ==========================================
    # GET BY FINGERPRINT
    # ==========================================

    def get_by_fingerprint(
        self,
        fingerprint: str,
    ):

        response = (
            self.client
            .table(self.table_name)
            .select("*")
            .eq(
                "fingerprint",
                fingerprint
            )
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]

    # ==========================================
    # CREATE
    # ==========================================

    def create(
        self,
        fingerprint: AIOperationFingerprint,
    ):

        response = (
            self.client
            .table(self.table_name)
            .insert(
                fingerprint.model_dump(
                    mode="json"
                )
            )
            .execute()
        )

        return response.data[0]

    # ==========================================
    # IS EXPIRED
    # ==========================================

    def is_expired(
        self,
        fingerprint: dict,
    ):

        expires_at = (
            fingerprint.get(
                "expires_at"
            )
        )

        if not expires_at:
            return False

        expires_at = (
            datetime.fromisoformat(
                expires_at.replace(
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
