from app.db.supabase_client import (
    supabase
)
from datetime import UTC, datetime

from app.schemas.ai_interpretation import (
    AIInterpretation,
)


class AIInterpretationRepository:

    def __init__(self):

        self.client = (
            supabase
        )
        self.table_name = (
            "ai_interpretations"
        )

    # =====================================
    # CREATE
    # =====================================

    def create_interpretation(
        self,
        interpretation: AIInterpretation | dict,
    ):
        if isinstance(interpretation, dict):
            payload = interpretation
        else:
            payload = interpretation.model_dump(
                exclude_none=True
            )

        response = (
            self.client
            .table(self.table_name)
            .insert(payload)
            .execute()
        )

        return response.data[0]

    # =====================================
    # GETTERS
    # =====================================

    def get_review_by_id(
        self,
        interpretation_id: str,
    ):
        response = (
            self.client
            .table(self.table_name)
            .select("*")
            .eq(
                "id",
                interpretation_id
            )
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]

    # =====================================
    # PENDING REVIEWS
    # =====================================

    def get_pending_reviews(self):

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

        return (
            response.data
            or []
        )

    def get_all_reviews(self):

        response = (
            self.client
            .table(self.table_name)
            .select("*")
            .execute()
        )

        return (
            response.data
            or []
        )

    # =====================================
    # PROJECT REVIEWS
    # =====================================

    def get_reviews_by_project(
        self,
        project_id: str
    ):

        # =========================
        # GET REPORT IDS
        # =========================

        reports_response = (
            self.client
            .table("reports")
            .select("id")
            .eq(
                "project_id",
                project_id
            )
            .execute()
        )

        reports = (
            reports_response.data
            or []
        )

        report_ids = [
            report["id"]
            for report in reports
        ]

        if not report_ids:
            return []

        # =========================
        # GET FINDINGS
        # =========================

        findings_response = (
            self.client
            .table("findings")
            .select("id, report_id")
            .execute()
        )

        findings = (
            findings_response.data
            or []
        )

        filtered_findings = [
            finding
            for finding in findings
            if finding["report_id"]
            in report_ids
        ]

        finding_ids = [
            finding["id"]
            for finding in filtered_findings
        ]

        if not finding_ids:
            return []

        # =========================
        # GET REVIEWS
        # =========================

        reviews_response = (
            self.client
            .table(self.table_name)
            .select("*")
            .execute()
        )

        reviews = (
            reviews_response.data
            or []
        )

        filtered_reviews = [
            review
            for review in reviews
            if review["finding_id"]
            in finding_ids
        ]

        return filtered_reviews

    # =====================================
    # STATUS MANAGEMENT
    # =====================================

    def approve_interpretation(
        self,
        interpretation_id: str,
        reviewed_by: str,
        review_notes: str | None = None,
    ):
        update_payload = {
            "review_status": "APPROVED",
            "reviewed_by": reviewed_by,
            "reviewed_at": (
                datetime
                .now(UTC)
                .isoformat()
            ),
            "review_notes": review_notes,
        }

        response = (
            self.client
            .table(self.table_name)
            .update(update_payload)
            .eq(
                "id",
                interpretation_id
            )
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]

    def reject_interpretation(
        self,
        interpretation_id: str,
        reviewed_by: str,
        review_notes: str | None = None,
    ):
        update_payload = {
            "review_status": "REJECTED",
            "reviewed_by": reviewed_by,
            "reviewed_at": (
                datetime
                .now(UTC)
                .isoformat()
            ),
            "review_notes": review_notes,
        }

        response = (
            self.client
            .table(self.table_name)
            .update(update_payload)
            .eq(
                "id",
                interpretation_id
            )
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]

    def assign_reviewer(
        self,
        interpretation_id: str,
        reviewer_id: str,
    ):
        response = (
            self.client
            .table(self.table_name)
            .update({
                "assigned_reviewer":
                    reviewer_id,
            })
            .eq(
                "id",
                interpretation_id
            )
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]

    def apply_human_override(
        self,
        interpretation_id: str,
        overridden_by: str,
        override_reason: str,
    ):
        response = (
            self.client
            .table(self.table_name)
            .update({
                "review_status":
                    "OVERRIDDEN",
                "overridden_by":
                    overridden_by,
                "override_reason":
                    override_reason,
                "overridden_at":
                    datetime
                    .now(UTC)
                    .isoformat(),
            })
            .eq(
                "id",
                interpretation_id
            )
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]

    def review_recommendation(
        self,
        interpretation_id: str,
        decision: str,
        reviewed_by: str,
        review_notes: str | None = None,
    ):
        response = (
            self.client
            .table(self.table_name)
            .update({
                "recommendation_review_status":
                    decision,
                "recommendation_reviewed_by":
                    reviewed_by,
                "recommendation_review_notes":
                    review_notes,
                "recommendation_reviewed_at":
                    datetime
                    .now(UTC)
                    .isoformat(),
            })
            .eq(
                "id",
                interpretation_id
            )
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]