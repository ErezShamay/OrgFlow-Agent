from app.repositories.operational_action_repository import (
    OperationalActionRepository,
)

from app.repositories.ai_interpretation_repository import (
    AIInterpretationRepository,
)


class ProjectInsightsService:

    @staticmethod
    def generate_project_insights(
        project_id: str
    ):

        insights = []

        reviews = (
            AIInterpretationRepository()
            .get_reviews_by_project(
                project_id
            )
        )

        actions = (
            OperationalActionRepository()
            .get_open_actions_by_project(
                project_id
            )
        )

        # =========================
        # HIGH RISK REVIEWS
        # =========================

        high_risk_reviews = [

            review

            for review in reviews

            if (
                str(
                    review.get(
                        "tenant_risk",
                        ""
                    )
                )
                .lower()
                .find("high") >= 0
            )
        ]

        if len(high_risk_reviews) > 0:

            insights.append({
                "type": "RISK",

                "title":
                    "זוהו ביקורות בסיכון גבוה",

                "description":
                    f"{len(high_risk_reviews)} ביקורות דורשות טיפול מיידי",
            })

        # =========================
        # TOO MANY OPEN ACTIONS
        # =========================

        if len(actions) >= 5:

            insights.append({
                "type": "OPERATIONS",

                "title":
                    "עומס פעולות פתוחות",

                "description":
                    f"קיימות {len(actions)} פעולות פתוחות בפרויקט",
            })

        # =========================
        # NO INSIGHTS
        # =========================

        if len(insights) == 0:

            insights.append({
                "type": "POSITIVE",

                "title":
                    "הפרויקט יציב תפעולית",

                "description":
                    "לא זוהו חריגות משמעותיות",
            })

        return insights