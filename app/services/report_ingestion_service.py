from app.tools.project_tool import (
    ProjectTool
)

from app.services.finding_extraction_service import (
    FindingExtractionService,
)

from app.services.ai_enrichment_service import (
    AIEnrichmentService,
)

from app.repositories.finding_repository import (
    FindingRepository
)

from app.repositories.ai_interpretation_repository import (
    AIInterpretationRepository
)

from app.repositories.weekly_report_repository import (
    WeeklyReportRepository
)

from app.services.email_classifier_service import (
    EmailClassifierService
)


class ReportIngestionService:

    def __init__(self):

        self.project_tool = (
            ProjectTool()
        )

        self.report_repository = (
            WeeklyReportRepository()
        )

        self.finding_repository = (
            FindingRepository()
        )

        self.ai_interpretation_repository = (
            AIInterpretationRepository()
        )

        self.classifier = (
            EmailClassifierService()
        )

        self.finding_extraction_service = (
            FindingExtractionService()
        )

        self.ai_enrichment_service = (
            AIEnrichmentService()
        )

    def process_message(
        self,
        message
    ):

        subject = (
            message.get(
                "subject",
                ""
            )
        )

        body = (
            message.get(
                "body",
                ""
            )
        )

        projects = (
            self.project_tool
            .get_all_projects()
        )

        matched_project = None

        for project in projects:

            project_name = (
                project[
                    "project_name"
                ]
            )

            if (
                project_name
                in subject
            ):

                matched_project = (
                    project
                )

                break

        if not matched_project:

            return {
                "status":
                    "NO_PROJECT_MATCH"
            }

        if not matched_project.get("id"):

            return {
                "status":
                    "SUCCESS",

                "project":
                    matched_project,

                "message":
                    message,
            }

        classification = (
            self.classifier
            .classify(message)
        )

        created_report = (
            self.report_repository
            .create_report(
                project_id=
                matched_project["id"],

                report_source=
                "EMAIL",

                email_subject=
                subject
            )
        )

        findings = (
            self.finding_extraction_service
            .extract_findings(
                report_text=body,

                report_id=str(
                    created_report["id"]
                ),

                project_id=str(
                    matched_project["id"]
                )
            )
        )

        created_findings = []

        for finding in findings:

            created_finding = (
                self.finding_repository
                .create_finding(
                    finding
                )
            )

            enrichment_data = (
                self.ai_enrichment_service
                .enrich_finding(
                    finding
                )
            )

            interpretation = (
                self.ai_enrichment_service
                .build_interpretation(
                    finding_id=str(
                        created_finding["id"]
                    ),

                    enrichment_data=
                    enrichment_data
                )
            )

            created_interpretation = (
                self.ai_interpretation_repository
                .create_interpretation(
                    interpretation
                )
            )

            created_findings.append({
                "finding":
                    created_finding,

                "ai_interpretation":
                    created_interpretation
            })

        print("\n=== FINDINGS ===")

        for item in created_findings:
            print(item)

        return {
            "status":
                "SUCCESS",

            "classification":
                classification,

            "project":
                matched_project,

            "message":
                message,

            "report":
                created_report,

            "findings":
                created_findings
        }
