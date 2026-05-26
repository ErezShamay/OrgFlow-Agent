from app.db.supabase_client import (
    supabase
)

from app.repositories.workspace_activity_repository import (
    WorkspaceActivityRepository,
)

from app.services.report_text_extraction_service import (
    ReportTextExtractionService,
)


class ReportProcessingService:

    @staticmethod
    def process_uploaded_report(
        project_id: str,
        filename: str,
        file_path: str,
    ):

        supabase = (
            SupabaseClient
            .get_client()
        )

        report_text = (
    ReportTextExtractionService
    .extract_text(
        file_path
    )
)

        # =========================
        # MOCK AI REVIEW
        # =========================

        supabase.table(
            "ai_interpretations"
        ).insert({

            "project_id":
                project_id,

            "business_impact":
                report_text[:500]
                if report_text
                else "לא זוהה תוכן",

            "tenant_risk":
                "HIGH",

            "recommended_action":
                "נדרש טיפול מול קבלן הביצוע",

            "review_status":
                "PENDING",

        }).execute()

        # =========================
        # WORKSPACE ACTIVITY
        # =========================

        WorkspaceActivityRepository.create_activity(
            project_id=project_id,

            activity_type=
                "REPORT_UPLOAD",

            title=
                "דוח חדש הועלה למערכת",

            description=
                f"הועלה הקובץ: {filename}",
        )

        WorkspaceActivityRepository.create_activity(
            project_id=project_id,

            activity_type=
                "AI_ANALYSIS",

            title=
                "AI יצר ביקורת חדשה",

            description=
                "נוצרה ביקורת תפעולית חדשה לבדיקה",
        )

        return {
            "success": True
        }