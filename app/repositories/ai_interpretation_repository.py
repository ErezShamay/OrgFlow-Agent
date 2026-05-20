from datetime import datetime

from app.db.supabase_client import (
    SupabaseClient
)

from app.schemas.ai_interpretation import (
    AIInterpretation
)


class AIInterpretationRepository:

    def __init__(self):

        self.client = (
            SupabaseClient
            .get_client()
        )

        self.table_name = (
            "ai_interpretations"
        )

    def create_interpretation(
        self,
        interpretation: AIInterpretation
    ):

        payload = (
            interpretation.model_dump(
                exclude_none=True
            )
        )

        response = (
            self.client
            .table(self.table_name)
            .insert(payload)
            .execute()
        )

        return response.data[0]

    def get_pending_reviews(
        self
    ):

        response = (
            self.client
            .table(self.table_name)
            .select("*")
            .eq(
                "review_status",
                "PENDING"
            )
            .execute()
        )

        return response.data

    def approve_interpretation(
        self,
        interpretation_id: str,
        reviewed_by: str,
        review_notes: str | None = None
    ):

        response = (
            self.client
            .table(self.table_name)
            .update({
                "review_status":
                    "APPROVED",

                "reviewed_by":
                    reviewed_by,

                "reviewed_at":
                    datetime.utcnow()
                    .isoformat(),

                "review_notes":
                    review_notes
            })
            .eq(
                "id",
                interpretation_id
            )
            .execute()
        )

        return response.data[0]

    def reject_interpretation(
        self,
        interpretation_id: str,
        reviewed_by: str,
        review_notes: str | None = None
    ):

        response = (
            self.client
            .table(self.table_name)
            .update({
                "review_status":
                    "REJECTED",

                "reviewed_by":
                    reviewed_by,

                "reviewed_at":
                    datetime.utcnow()
                    .isoformat(),

                "review_notes":
                    review_notes
            })
            .eq(
                "id",
                interpretation_id
            )
            .execute()
        )

        return response.data[0]