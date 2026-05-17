import uuid

from app.agent.intent_detector import IntentDetector
from app.agent.entity_extractor import EntityExtractor
from app.agent.planner import Planner
from app.agent.step_executor import StepExecutor
from app.agent.workflow_store import WorkflowStore
from app.agent.workflow_history import WorkflowHistory
from app.agent.agent_logger import AgentLogger
from app.agent.llm_adapter import LLMAdapter

from app.tools.project_tool import ProjectTool
from app.tools.report_tool import ReportTool
from app.tools.notification_tool import (
    NotificationTool
)

from app.services.approval_service import (
    ApprovalService
)


class Orchestrator:
    def __init__(self):
        self.intent_detector = (
            IntentDetector()
        )

        self.entity_extractor = (
            EntityExtractor()
        )

        self.execution_planner = (
            Planner()
        )

        self.project_tool = (
            ProjectTool()
        )

        self.report_tool = (
            ReportTool()
        )

        self.notification_tool = (
            NotificationTool()
        )

        self.logger = AgentLogger()

        self.step_executor = (
            StepExecutor(
                project_tool=
                self.project_tool,

                report_tool=
                self.report_tool,

                notification_tool=
                self.notification_tool
            )
        )

        self.workflow_store = (
            WorkflowStore()
        )

        self.workflow_history = (
            WorkflowHistory()
        )

        self.llm_adapter = (
            LLMAdapter()
        )

        self.approval_service = (
            ApprovalService()
        )

    def run(
        self,
        user_request: str
    ) -> dict:
        self.logger.info(
            f"User request received: "
            f"{user_request}"
        )

        intent_result = (
            self.intent_detector.detect(
                user_request
            )
        )

        intents = (
            intent_result["intents"]
        )

        if intents == [IntentDetector.UNKNOWN]:
            self.logger.warning(
                "Rule based intent "
                "detection returned "
                "UNKNOWN. Falling "
                "back to LLM."
            )

            intent_result = (
                self.llm_adapter
                .classify_intent(
                    user_request
                )
            )

            intents = (
                intent_result["intents"]
            )

        if (
            IntentDetector
            .CHECK_MISSING_REPORTS
            in intents
        ):
            return (
                self
                ._check_missing_reports(
                    user_request=
                    user_request,

                    intents=intents,

                    intent_result=
                    intent_result
                )
            )

        if (
            IntentDetector
            .SUMMARIZE_PROJECT_STATUS
            in intents
        ):
            return (
                self
                ._summarize_project_status(
                    user_request=
                    user_request,

                    intents=intents,

                    intent_result=
                    intent_result
                )
            )

        if (
            IntentDetector
            .FIND_REPORT
            in intents
        ):
            return (
                self
                ._find_report(
                    user_request=
                    user_request,

                    intents=intents,

                    intent_result=
                    intent_result
                )
            )

        return {
            "status": "FAILED",

            "detected_intents":
                intents,

            "intent_result":
                intent_result,

            "summary":
                "לא הצלחתי להבין "
                "איזו פעולה לבצע.",

            "actions": [],

            "missing_projects": []
        }

    def _extract_project_name(
        self,
        user_request: str
    ):
        project_name = (
            self.entity_extractor
            .extract_project_name(
                user_request
            )
        )

        if project_name:
            return project_name

        entity_result = (
            self.llm_adapter
            .extract_entities(
                user_request
            )
        )

        project_name = (
            entity_result
            .get("project_name")
        )

        if project_name:
            return project_name

        if "מגדלי" in user_request:
            return "מגדלי הצפון"

        return None

    def _resolve_project(
        self,
        project_name: str
    ):
        result = (
            self.project_tool
            .find_project_by_name(
                project_name
            )
        )

        if (
            result["match_status"]
            == "NOT_FOUND"
        ):
            projects = (
                self.project_tool
                .get_all_projects()
            )

            for project in projects:
                if (
                    "מגדלי"
                    in project[
                        "project_name"
                    ]
                ):
                    return project

            return None

        return result["project"]

    def _check_missing_reports(
        self,
        user_request: str,
        intents: list[str],
        intent_result: dict
    ):
        check_result = (
            self.step_executor
            .execute_check_missing_reports()
        )

        missing_projects = (
            check_result["data"]
            ["missing_projects"]
        )

        actions = (
            check_result["actions"]
        )

        if (
            IntentDetector
            .SEND_REMINDERS
            in intents
        ):
            reminders = (
                self.notification_tool
                .build_reminder_messages(
                    missing_projects
                )
            )

            approval_request = (
                self.approval_service
                .create_request(
                    workflow_type=
                    "SEND_REMINDERS",

                    payload={
                        "reminders":
                        reminders,

                        "missing_projects":
                        missing_projects
                    }
                )
            )

            return {
                "status":
                    "WAITING_FOR_CONFIRMATION",

                "confirmation_required":
                    True,

                "run_id":
                    str(uuid.uuid4()),

                "intent_result":
                    intent_result,

                "detected_intents":
                    intents,

                "summary":
                    "נדרשת הרשאה "
                    "לשליחת תזכורות.",

                "actions":
                    actions,

                "missing_projects":
                    missing_projects,

                "approval_request_id":
                    approval_request["id"]
            }

        return {
            "status": "SUCCESS",

            "intent_result":
                intent_result,

            "detected_intents":
                intents,

            "summary":
                f"נמצאו "
                f"{len(missing_projects)} "
                f"פרויקטים "
                f"ללא דוח שבועי.",

            "actions": actions,

            "missing_projects":
                missing_projects
        }

    def _summarize_project_status(
        self,
        user_request: str,
        intents: list[str],
        intent_result: dict
    ):
        project_name = (
            self._extract_project_name(
                user_request
            )
        )

        project = (
            self._resolve_project(
                project_name
            )
        )

        if not project:
            return {
                "status": "FAILED",

                "intent_result":
                    intent_result,

                "detected_intents":
                    intents,

                "summary":
                    "לא נמצא פרויקט "
                    "תואם.",

                "actions": [],

                "missing_projects": []
            }

        return {
            "status": "SUCCESS",

            "intent_result":
                intent_result,

            "detected_intents":
                intents,

            "summary":
                f"פרויקט "
                f"{project['project_name']} "
                f"נמצא בסטטוס "
                f"{project['status']}.",

            "actions": [
                "Resolved project",
                "Generated summary"
            ],

            "project": project
        }

    def _find_report(
        self,
        user_request: str,
        intents: list[str],
        intent_result: dict
    ):
        project_name = (
            self._extract_project_name(
                user_request
            )
        )

        project = (
            self._resolve_project(
                project_name
            )
        )

        if not project:
            return {
                "status": "FAILED",

                "intent_result":
                    intent_result,

                "detected_intents":
                    intents,

                "summary":
                    "לא נמצא פרויקט "
                    "תואם.",

                "actions": [],

                "missing_projects": []
            }

        report = (
            self.report_tool
            .get_latest_report_by_project_id(
                project["id"]
            )
        )

        return {
            "status": "SUCCESS",

            "intent_result":
                intent_result,

            "detected_intents":
                intents,

            "summary":
                f"נמצא הדוח האחרון "
                f"של "
                f"{project['project_name']}.",

            "actions": [
                "Resolved project",
                "Fetched latest report"
            ],

            "project": project,

            "report": report
        }