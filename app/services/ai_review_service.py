from app.repositories.ai_interpretation_repository import (
    AIInterpretationRepository
)


class AIReviewService:

    def __init__(self):

        self.repository = (
            AIInterpretationRepository()
        )

    def get_pending_reviews(
        self
    ):

        return (
            self.repository
            .get_pending_reviews()
        )

    def approve_review(
        self,
        interpretation_id: str,
        reviewed_by: str,
        review_notes: str | None = None
    ):

        return (
            self.repository
            .approve_interpretation(
                interpretation_id=
                    interpretation_id,

                reviewed_by=
                    reviewed_by,

                review_notes=
                    review_notes
            )
        )

    def reject_review(
        self,
        interpretation_id: str,
        reviewed_by: str,
        review_notes: str | None = None
    ):

        return (
            self.repository
            .reject_interpretation(
                interpretation_id=
                    interpretation_id,

                reviewed_by=
                    reviewed_by,

                review_notes=
                    review_notes
            )
        )