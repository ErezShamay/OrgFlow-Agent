from app.repositories.ai_interpretation_repository import (
    AIInterpretationRepository
)

from app.repositories.finding_repository import (
    FindingRepository
)

from app.repositories.operational_action_repository import (
    OperationalActionRepository
)

from app.services.action_generation_service import (
    ActionGenerationService
)


class AIReviewService:

    def __init__(self):

        self.repository = (
            AIInterpretationRepository()
        )

        self.finding_repository = (
            FindingRepository()
        )

        self.action_repository = (
            OperationalActionRepository()
        )

        self.action_generation_service = (
            ActionGenerationService()
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

        approved = (
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

        finding = (
            self.finding_repository
            .get_finding_by_id(
                approved[
                    "finding_id"
                ]
            )
        )

        action = (
            self.action_generation_service
            .generate_action(
                interpretation=
                    approved,

                finding=
                    finding
            )
        )

        created_action = (
            self.action_repository
            .create_action(
                action
            )
        )

        return {
            "approved_interpretation":
                approved,

            "created_action":
                created_action
        }

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