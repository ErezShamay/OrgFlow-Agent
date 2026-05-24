from app.schemas.operational_action import (
    OperationalAction
)


class ActionGenerationService:

    def generate_action(
        self,
        interpretation: dict,
        finding: dict
    ) -> OperationalAction:

        finding_type = (
            finding[
                "finding_type"
            ]
        )

        action_type = (
            self._resolve_action_type(
                finding_type
            )
        )

        return OperationalAction(
            interpretation_id=
                interpretation["id"],

            action_type=
                action_type,

            title=
                interpretation[
                    "recommended_action"
                ],

            description=
                interpretation[
                    "business_impact"
                ],
        )

    def _resolve_action_type(
        self,
        finding_type: str
    ) -> str:

        mapping = {
            "schedule_delay":
                "FOLLOW_UP",

            "approval_delay":
                "ESCALATION",

            "quality_issue":
                "SITE_INSPECTION",
        }

        return mapping.get(
            finding_type,
            "GENERAL"
        )