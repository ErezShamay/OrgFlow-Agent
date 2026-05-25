from app.db.supabase_client import (
    SupabaseClient
)


class AIInterpretationRepository:

    def __init__(self):

        self.client = (
            SupabaseClient
            .get_client()
        )

    # =====================================
    # PENDING REVIEWS
    # =====================================

    def get_pending_reviews(self):

        response = (
            self.client
            .table("ai_interpretations")
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
            .table("ai_interpretations")
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