from app.tools.project_tool import (
    ProjectTool
)

from app.services.finding_extraction_service import (
    FindingExtractionService,
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

        self.classifier = (
            EmailClassifierService()
        )

        self.finding_extraction_service = (
            FindingExtractionService()
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

        classification = (
            self.classifier
            .classify(message)
        )

        # backward compatibility
        if (
            classification[
                "classification"
            ]
            == "UNKNOWN"
        ):

            return {
                "status":
                    "SUCCESS",

                "project":
                    matched_project,

                "message":
                    message,

                "classification":
                    classification,

                "report":
                    None,

                "findings":
                    []
            }

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

        print("\n=== FINDINGS ===")

        for finding in findings:
            print(
                finding.model_dump()
            )

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
                findings
        }