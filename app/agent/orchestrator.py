import uuid

from app.agent.intent_detector import IntentDetector
from app.agent.workflow_store import WorkflowStore
from app.agent.workflow_history import WorkflowHistory
from app.agent.entity_extractor import EntityExtractor
from app.agent.planner import Planner
from app.agent.step_executor import StepExecutor
from app.agent.response_builder import ResponseBuilder
from app.agent.agent_logger import AgentLogger
from app.agent.llm_adapter import LLMAdapter

from app.tools.project_tool import ProjectTool
from app.tools.report_tool import ReportTool
from app.tools.notification_tool import NotificationTool


class Orchestrator:
    def __init__(self):
        self.intent_detector = IntentDetector()
        self.entity_extractor = EntityExtractor()
        self.planner = Planner()
        self.response_builder = ResponseBuilder()
        self.logger = AgentLogger()
        self.llm_adapter = LLMAdapter()

        self.project_tool = ProjectTool()
        self.report_tool = ReportTool()
        self.notification_tool = NotificationTool()

        self.step_executor = StepExecutor(
            project_tool=self.project_tool,
            report_tool=self.report_tool,
            notification_tool=self.notification_tool
        )

        self.workflow_store = WorkflowStore()
        self.workflow_history = WorkflowHistory()

    def run(self, user_request: str) -> dict:
        self.logger.info(f"User request received: {user_request}")

        intent_result = self.intent_detector.detect(user_request)

        if IntentDetector.UNKNOWN in intent_result["intents"]:
            self.logger.warning(
                "Rule based intent detection returned UNKNOWN. Falling back to LLM."
            )

            intent_result = self.llm_adapter.classify_intent(
                user_request
            )

        intents = intent_result["intents"]

        self.logger.info(
            f"Detected intents: {intents}, "
            f"confidence={intent_result['confidence']}, "
            f"source={intent_result['source']}"
        )

        plan = self.planner.build_plan(intents)
        self.logger.info(f"Execution plan created: {plan}")

        if IntentDetector.CHECK_MISSING_REPORTS in intents:
            return self._check_missing_reports(
                user_request=user_request,
                intents=intents,
                plan=plan,
                intent_result=intent_result
            )

        if IntentDetector.SUMMARIZE_PROJECT_STATUS in intents:
            return self._summarize_project_status(
                user_request=user_request,
                intents=intents,
                plan=plan,
                intent_result=intent_result
            )

        if IntentDetector.FIND_REPORT in intents:
            return self._find_report(
                user_request=user_request,
                intents=intents,
                plan=plan,
                intent_result=intent_result
            )

        self.logger.warning("No supported workflow found for request")

        return self.response_builder.failed(
            summary="לא הצלחתי להבין איזו פעולה לבצע.",
            detected_intents=intents,
            execution_plan=plan,
            extra={
                "intent_result": intent_result
            }
    )

    def confirm(self, run_id: str) -> dict:
        self.logger.info(f"Confirmation received for run_id: {run_id}")

        workflow = self.workflow_store.get(run_id)

        if not workflow:
            self.logger.error(f"Workflow not found: {run_id}")
            return {
                "run_id": run_id,
                "status": "FAILED",
                "summary": "Workflow not found."
            }

        if workflow["type"] == "SEND_REMINDERS":
            sent = self.notification_tool.send_reminders(workflow["reminders"])
            self.workflow_store.delete(run_id)

            summary = f"נשלחו {len(sent)} תזכורות."
            actions = [
                "User confirmed pending workflow",
                "Sent reminder notifications",
                "Deleted pending workflow"
            ]

            self.workflow_history.add_run({
                "run_id": run_id,
                "type": "SEND_REMINDERS",
                "status": "SUCCESS",
                "summary": summary,
                "actions": actions,
                "execution_plan": workflow.get("execution_plan"),
                "intent_result": workflow.get("intent_result")
            })

            self.logger.info(summary)

            return self.response_builder.success(
                summary=summary,
                detected_intents=["SEND_REMINDERS"],
                actions=actions,
                execution_plan=workflow.get("execution_plan"),
                extra={
                    "run_id": run_id,
                    "sent_notifications": sent,
                    "intent_result": workflow.get("intent_result")
                }
            )

        self.logger.error(f"Unknown workflow type: {workflow['type']}")

        return {
            "run_id": run_id,
            "status": "FAILED",
            "summary": "Unknown workflow type."
        }

    def get_history(self) -> list[dict]:
        return self.workflow_history.get_all()

    def _resolve_project(
        self,
        project_name: str,
        actions: list[str],
        intents: list[str],
        plan: dict
    ):
        self.logger.info(f"Resolving project: {project_name}")

        project_result = self.project_tool.find_project_by_name(project_name)
        actions.append("Searched project by name")

        if project_result["match_status"] == "MULTIPLE_MATCHES":
            self.logger.warning(
                f"Multiple project matches found: {project_result['suggestions']}"
            )

            return None, self.response_builder.needs_clarification(
                summary="מצאתי כמה פרויקטים דומים.",
                detected_intents=intents,
                next_step="לאיזה פרויקט התכוונת?",
                actions=actions,
                execution_plan=plan,
                extra={
                    "project_name": project_name,
                    "suggestions": project_result["suggestions"]
                }
            )

        if project_result["match_status"] == "NOT_FOUND":
            self.logger.warning(f"Project not found: {project_name}")

            return None, self.response_builder.failed(
                summary=f"לא מצאתי פרויקט בשם {project_name}.",
                detected_intents=intents,
                actions=actions,
                execution_plan=plan,
                extra={
                    "project_name": project_name
                }
            )

        self.logger.info(
            f"Project resolved: {project_result['project']['project_name']} "
            f"({project_result['match_status']})"
        )

        return project_result["project"], None

    def _check_missing_reports(
        self,
        user_request: str,
        intents: list[str],
        plan: dict,
        intent_result: dict
    ) -> dict:
        self.logger.info("Starting workflow: CHECK_MISSING_REPORTS")

        check_result = self.step_executor.execute_check_missing_reports()

        missing_projects = check_result["data"]["missing_projects"]
        actions = check_result["actions"]

        self.logger.info(f"Missing projects found: {len(missing_projects)}")

        if IntentDetector.SEND_REMINDERS in intents:
            self.logger.info("Preparing reminder messages")

            reminders_result = self.step_executor.execute_build_reminders(
                missing_projects
            )

            reminders = reminders_result["data"]["reminders"]
            combined_actions = actions + reminders_result["actions"]
            run_id = str(uuid.uuid4())

            self.workflow_store.save(run_id, {
                "type": "SEND_REMINDERS",
                "reminders": reminders,
                "execution_plan": plan,
                "intent_result": intent_result
            })

            summary = (
                f"נמצאו {len(missing_projects)} פרויקטים ללא דוח שבועי. "
                f"המערכת מוכנה לשלוח {len(reminders)} תזכורות."
            )

            self.workflow_history.add_run({
                "run_id": run_id,
                "type": "SEND_REMINDERS",
                "status": "WAITING_FOR_CONFIRMATION",
                "summary": (
                    f"נמצאו {len(missing_projects)} פרויקטים ללא דוח שבועי. "
                    f"ממתין לאישור לשליחת {len(reminders)} תזכורות."
                ),
                "actions": combined_actions,
                "execution_plan": plan,
                "intent_result": intent_result
            })

            self.logger.info(f"Workflow waiting for confirmation. run_id={run_id}")

            return self.response_builder.waiting_for_confirmation(
                run_id=run_id,
                summary=summary,
                detected_intents=intents,
                confirmation_message="האם לשלוח את התזכורות עכשיו?",
                actions=combined_actions,
                execution_plan=plan,
                extra={
                    "missing_projects": missing_projects,
                    "pending_reminders": reminders,
                    "intent_result": intent_result
                }
            )

        summary = f"נמצאו {len(missing_projects)} פרויקטים ללא דוח שבועי."

        self.workflow_history.add_run({
            "type": "CHECK_MISSING_REPORTS",
            "status": "SUCCESS",
            "summary": summary,
            "actions": actions,
            "execution_plan": plan,
            "intent_result": intent_result
        })

        self.logger.info("Workflow completed: CHECK_MISSING_REPORTS")

        return self.response_builder.success(
            summary=summary,
            detected_intents=intents,
            actions=actions,
            execution_plan=plan,
            extra={
                "missing_projects": missing_projects,
                "confirmation_required": False,
                "intent_result": intent_result
            }
        )

    def _summarize_project_status(
        self,
        user_request: str,
        intents: list[str],
        plan: dict,
        intent_result: dict
    ) -> dict:
        self.logger.info("Starting workflow: SUMMARIZE_PROJECT_STATUS")

        project_name = self.entity_extractor.extract_project_name(user_request)
        actions = ["Extracted project name from user request"]

        if not project_name:
            self.logger.warning("Project name missing")

            return self.response_builder.needs_clarification(
                summary="חסר שם פרויקט.",
                detected_intents=intents,
                next_step="לאיזה פרויקט תרצה שאסכם סטטוס?",
                actions=actions,
                execution_plan=plan,
                extra={
                    "intent_result": intent_result
                }
            )

        project, error_response = self._resolve_project(
            project_name=project_name,
            actions=actions,
            intents=intents,
            plan=plan
        )

        if error_response:
            error_response["intent_result"] = intent_result
            return error_response

        latest_report = self.report_tool.get_latest_report_by_project_id(
            project["project_id"]
        )
        actions.append("Loaded latest report for project")

        if not latest_report:
            self.logger.warning(f"No reports found for project: {project_name}")

            return self.response_builder.failed(
                summary=f"הפרויקט {project_name} נמצא, אבל לא נמצאו עבורו דוחות.",
                detected_intents=intents,
                actions=actions,
                execution_plan=plan,
                extra={
                    "project": project,
                    "intent_result": intent_result
                }
            )

        summary = (
            f"סטטוס פרויקט {project['project_name']}:\n"
            f"- מפקח אחראי: {project['supervisor_name']}\n"
            f"- דוח אחרון: {latest_report['file_name']}\n"
            f"- תאריך קבלה: {latest_report['received_date']}\n"
            f"- סטטוס כללי: התקבל דוח שבועי אחרון במערכת."
        )

        self.workflow_history.add_run({
            "type": "SUMMARIZE_PROJECT_STATUS",
            "status": "SUCCESS",
            "summary": summary,
            "actions": actions,
            "execution_plan": plan,
            "intent_result": intent_result
        })

        self.logger.info("Workflow completed: SUMMARIZE_PROJECT_STATUS")

        return self.response_builder.success(
            summary=summary,
            detected_intents=intents,
            actions=actions,
            execution_plan=plan,
            extra={
                "project": project,
                "latest_report": latest_report,
                "intent_result": intent_result
            }
        )

    def _find_report(
        self,
        user_request: str,
        intents: list[str],
        plan: dict,
        intent_result: dict
    ) -> dict:
        self.logger.info("Starting workflow: FIND_REPORT")

        project_name = self.entity_extractor.extract_project_name(user_request)
        actions = ["Extracted project name from user request"]

        if not project_name:
            self.logger.warning("Project name missing")

            return self.response_builder.needs_clarification(
                summary="חסר שם פרויקט.",
                detected_intents=intents,
                next_step="לאיזה פרויקט תרצה שאמצא דוח?",
                actions=actions,
                execution_plan=plan,
                extra={
                    "intent_result": intent_result
                }
            )

        project, error_response = self._resolve_project(
            project_name=project_name,
            actions=actions,
            intents=intents,
            plan=plan
        )

        if error_response:
            error_response["intent_result"] = intent_result
            return error_response

        latest_report = self.report_tool.get_latest_report_by_project_id(
            project["project_id"]
        )
        actions.append("Loaded latest report for project")

        if not latest_report:
            self.logger.warning(f"No reports found for project: {project_name}")

            return self.response_builder.failed(
                summary=f"הפרויקט {project_name} נמצא, אבל לא נמצאו עבורו דוחות.",
                detected_intents=intents,
                actions=actions,
                execution_plan=plan,
                extra={
                    "project": project,
                    "intent_result": intent_result
                }
            )

        summary = (
            f"מצאתי את הדוח האחרון של פרויקט {project['project_name']}: "
            f"{latest_report['file_name']} "
            f"מתאריך {latest_report['received_date']}."
        )

        self.workflow_history.add_run({
            "type": "FIND_REPORT",
            "status": "SUCCESS",
            "summary": summary,
            "actions": actions,
            "execution_plan": plan,
            "intent_result": intent_result
        })

        self.logger.info("Workflow completed: FIND_REPORT")

        return self.response_builder.success(
            summary=summary,
            detected_intents=intents,
            actions=actions,
            execution_plan=plan,
            extra={
                "project": project,
                "latest_report": latest_report,
                "intent_result": intent_result
            }
        )