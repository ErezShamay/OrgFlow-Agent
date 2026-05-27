from hashlib import sha256
from uuid import uuid4

from datetime import (
    datetime,
    timedelta,
    timezone,
)

from app.repositories.project_repository import (
    ProjectRepository
)

from app.repositories.operational_action_repository import (
    OperationalActionRepository
)

from app.repositories.ai_operation_fingerprint_repository import (
    AIOperationFingerprintRepository
)

from app.repositories.ai_execution_log_repository import (
    AIExecutionLogRepository
)

from app.schemas.operational_action import (
    OperationalAction
)

from app.schemas.ai_operation_fingerprint import (
    AIOperationFingerprint
)

from app.schemas.ai_execution_log import (
    AIExecutionLog
)

from app.services.project_workspace_service import (
    ProjectWorkspaceService
)

from app.services.predictive_risk_service import (
    PredictiveRiskService
)

from app.services.automation_notification_service import (
    AutomationNotificationService
)

from app.services.ai_assignment_service import (
    AIAssignmentService
)

from app.services.ai_confidence_service import (
    AIConfidenceService
)

from app.services.ai_failure_classification_service import (
    AIFailureClassificationService
)


class AIAutomationService:

    def __init__(self):

        self.project_repository = (
            ProjectRepository()
        )

        self.workspace_service = (
            ProjectWorkspaceService()
        )

        self.predictive_risk_service = (
            PredictiveRiskService()
        )

        self.automation_notifications = (
            AutomationNotificationService()
        )

        self.operational_action_repository = (
            OperationalActionRepository()
        )

        self.ai_assignment_service = (
            AIAssignmentService()
        )

        self.ai_confidence_service = (
            AIConfidenceService()
        )

        self.ai_failure_classification_service = (
            AIFailureClassificationService()
        )

        self.fingerprint_repository = (
            AIOperationFingerprintRepository()
        )

        self.execution_log_repository = (
            AIExecutionLogRepository()
        )

    # ==========================================
    # MAIN LOOP
    # ==========================================

    def run_analysis_cycle(
        self,
    ):

        print(
            "[AI_AUTOMATION] Starting AI analysis cycle"
        )

        projects = (
            self.project_repository
            .get_all_projects()
        )

        processed_count = 0

        error_count = 0

        print(
            f"[AI_AUTOMATION] "
            f"Projects loaded: {len(projects)}"
        )

        for project in projects:

            try:

                self.process_project(
                    project
                )

                processed_count += 1

            except Exception as error:

                error_count += 1

                print(
                    "[AI_AUTOMATION] "
                    "Failed processing project:",
                    project.get("id"),
                    str(error),
                )

                self.log_ai_execution(

                    project_id=
                        project.get("id"),

                    execution_type=
                        "PROJECT_PROCESSING",

                    status=
                        "FAILED",

                    details={
                        "error": str(error),
                    },

                    error=
                        error,
                )

        print(
            "[AI_AUTOMATION] Analysis cycle completed"
        )

        return {

            "processed_count":
                processed_count,

            "error_count":
                error_count,

            "metadata":
                {
                    "project_count":
                        len(projects)
                },
        }

    # ==========================================
    # PROCESS PROJECT
    # ==========================================

    def process_project(
        self,
        project: dict,
    ):

        project_id = (
            project.get("id")
        )

        if not project_id:

            print(
                "[AI_AUTOMATION] "
                "Project missing id"
            )

            self.log_ai_execution(

                execution_type=
                    "PROJECT_PROCESSING_SKIPPED",

                status=
                    "SKIPPED",

                details={
                    "reason":
                        "missing_project_id",

                    "project_name":
                        project.get(
                            "project_name"
                        ),
                },
            )

            return

        workspace = (
            self.workspace_service
            .get_workspace(
                project_id
            )
        )

        health = (
            workspace.get(
                "health",
                {}
            )
        )

        risk_analysis = (
            self.predictive_risk_service
            .analyze_project_risk(
                project_id
            )
        )

        self.evaluate_operational_health(

            project=
                project,

            health=
                health,

            risk_analysis=
                risk_analysis,
        )

    # ==========================================
    # EVALUATE HEALTH
    # ==========================================

    def evaluate_operational_health(
        self,
        project: dict,
        health: dict,
        risk_analysis: dict,
    ):

        status = (
            health.get(
                "status"
            )
        )

        score = (
            health.get(
                "score",
                100
            )
        )

        risk_level = (
            risk_analysis.get(
                "risk_level",
                "LOW"
            )
        )

        confidence = (
            self.ai_confidence_service
            .calculate_confidence(

                health=
                    health,

                risk_analysis=
                    risk_analysis,
            )
        )

        print(

            "[AI_AUTOMATION] "

            f"Project: "
            f"{project['project_name']} | "

            f"Status: {status} | "

            f"Score: {score} | "

            f"Risk: {risk_level} | "

            f"Confidence: "
            f"{confidence['confidence_level']} "
            f"({confidence['score']})"
        )

        self.log_ai_execution(

            project_id=
                project["id"],

            execution_type=
                "RISK_EVALUATION",

            status=
                "SUCCESS",

            confidence=
                confidence,

            details={

                "status":
                    status,

                "score":
                    score,

                "risk_level":
                    risk_level,
            },
        )

        is_critical = (

            status == "CRITICAL"

            or score < 40

            or risk_level == "HIGH"
        )

        if not is_critical:

            self.log_ai_execution(

                project_id=
                    project["id"],

                execution_type=
                    "AI_DECISION",

                status=
                    "NO_ACTION_NEEDED",

                confidence=
                    confidence,

                details={
                    "decision":
                        "NO_ACTION_NEEDED",

                    "reason":
                        "project_not_critical",

                    "status":
                        status,

                    "score":
                        score,

                    "risk_level":
                        risk_level,
                },
            )

            return

        self.create_critical_project_activity(

            project=
                project,

            health=
                health,

            risk_analysis=
                risk_analysis,

            confidence=
                confidence,
        )

    # ==========================================
    # CREATE CRITICAL ACTIVITY
    # ==========================================

    def create_critical_project_activity(
        self,
        project: dict,
        health: dict,
        risk_analysis: dict,
        confidence: dict,
    ):

        description = (

            f"AI זיהה סיכון תפעולי גבוה "
            f"בפרויקט "
            f"{project['project_name']}.\n\n"

            f"Health Score: "
            f"{health.get('score')}\n"

            f"Risk Level: "
            f"{risk_analysis.get('risk_level')}\n"

            f"Confidence: "
            f"{confidence.get('confidence_level')} "
            f"({confidence.get('score')})"
        )

        self.automation_notifications.create_automation_activity(

            project_id=
                project["id"],

            activity_type=
                "AI_CRITICAL_RISK",

            title=
                "AI זיהה סיכון תפעולי",

            description=
                description,
        )

        print(
            "[AI_AUTOMATION] "
            "Critical risk detected:",
            project["project_name"]
        )

        should_auto_execute = (

            confidence.get(
                "score",
                0
            ) >= 75
        )

        if not should_auto_execute:

            self.log_ai_execution(

                project_id=
                    project["id"],

                execution_type=
                    "AUTO_EXECUTION_SKIPPED",

                status=
                    "LOW_CONFIDENCE",

                confidence=
                    confidence,

                details={
                    "reason":
                        "confidence_below_threshold",
                },
            )

            print(
                "[AI_AUTOMATION] "
                "Confidence too low for "
                "auto execution"
            )

            return

        self.log_ai_execution(

            project_id=
                project["id"],

            execution_type=
                "AUTO_EXECUTION_APPROVED",

            status=
                "SUCCESS",

            confidence=
                confidence,

            details={
                "decision":
                    "AUTO_EXECUTE",

                "reason":
                    "confidence_above_threshold",
            },
        )

        self.create_ai_operational_action(

            project=
                project,

            health=
                health,

            risk_analysis=
                risk_analysis,
        )

    # ==========================================
    # CREATE AI ACTION
    # ==========================================

    def create_ai_operational_action(
        self,
        project: dict,
        health: dict,
        risk_analysis: dict,
    ):

        fingerprint = (
            self.generate_risk_fingerprint(

                project=
                    project,

                health=
                    health,

                risk_analysis=
                    risk_analysis,
            )
        )

        existing_fingerprint = (
            self.fingerprint_repository
            .get_by_fingerprint(
                fingerprint
            )
        )

        if existing_fingerprint:

            is_expired = (
                self.fingerprint_repository
                .is_expired(
                    existing_fingerprint
                )
            )

            if not is_expired:

                self.log_ai_execution(

                    project_id=
                        project["id"],

                    execution_type=
                        "FINGERPRINT_BLOCKED",

                    status=
                        "SKIPPED",

                    details={
                        "fingerprint":
                            fingerprint,
                    },
                )

                print(
                    "[AI_AUTOMATION] "
                    "Fingerprint already processed:",
                    fingerprint
                )

                return

        existing_actions = (
            self.operational_action_repository
            .get_open_actions_by_project(
                project["id"]
            )
        )

        already_exists = any(

            action.get(
                "action_type"
            ) == "AI_OPERATIONAL_RISK"

            for action
            in existing_actions
        )

        if already_exists:

            self.log_ai_execution(

                project_id=
                    project["id"],

                execution_type=
                    "DUPLICATE_ACTION_BLOCKED",

                status=
                    "SKIPPED",
            )

            print(
                "[AI_AUTOMATION] "
                "AI action already exists:",
                project["project_name"]
            )

            return

        best_assignee = (
            self.ai_assignment_service
            .get_best_assignee(
                project["id"]
            )
        )

        self.log_ai_assignment_decision(

            project=
                project,

            best_assignee=
                best_assignee,
        )

        assigned_to = (
            best_assignee["id"]
            if best_assignee
            else None
        )

        action = OperationalAction(

            id=str(uuid4()),

            project_id=
                project["id"],

            title=
                (
                    "AI זיהה סיכון "
                    "תפעולי בפרויקט"
                ),

            description=
                (
                    f"AI זיהה סיכון גבוה "
                    f"בפרויקט "
                    f"{project['project_name']}.\n\n"

                    f"Health Score: "
                    f"{health.get('score')}\n"

                    f"Risk Level: "
                    f"{risk_analysis.get('risk_level')}"
                ),

            action_type=
                "AI_OPERATIONAL_RISK",

            status=
                "OPEN",

            priority=
                "HIGH",

            assigned_to=
                assigned_to,

            due_date=
                None,
        )

        created_action = (
            self.operational_action_repository
            .create_action(
                action
            )
        )

        self.log_ai_execution(

            project_id=
                project["id"],

            execution_type=
                "AI_ACTION_CREATED",

            status=
                "SUCCESS",

            details={

                "action_id":
                    created_action["id"],

                "assigned_to":
                    assigned_to,
            },
        )

        self.save_fingerprint(

            fingerprint=
                fingerprint,

            project_id=
                project["id"],
        )

        print(

            "[AI_AUTOMATION] "

            f"AI operational action created: "
            f"{created_action['id']}"
        )

        self.create_action_activity(
            project
        )

        self.handle_auto_assignment(

            project=
                project,

            best_assignee=
                best_assignee,
        )

    # ==========================================
    # SAVE FINGERPRINT
    # ==========================================

    def save_fingerprint(
        self,
        fingerprint: str,
        project_id: str,
    ):

        ai_fingerprint = (
            AIOperationFingerprint(

                id=str(uuid4()),

                fingerprint=
                    fingerprint,

                project_id=
                    project_id,

                operation_type=
                    "AI_OPERATIONAL_RISK",

                created_at=
                    datetime.now(
                        timezone.utc
                    ),

                expires_at=
                    (
                        datetime.now(
                            timezone.utc
                        )

                        + timedelta(
                            days=7
                        )
                    ),
            )
        )

        self.fingerprint_repository.create(
            ai_fingerprint
        )

    # ==========================================
    # CREATE ACTION ACTIVITY
    # ==========================================

    def create_action_activity(
        self,
        project: dict,
    ):

        self.automation_notifications.create_automation_activity(

            project_id=
                project["id"],

            activity_type=
                "AI_ACTION_CREATED",

            title=
                "AI יצר פעולה תפעולית",

            description=
                (
                    f"נוצרה פעולה אוטומטית "
                    f"עבור "
                    f"{project['project_name']}"
                ),
        )

    # ==========================================
    # HANDLE AUTO ASSIGNMENT
    # ==========================================

    def handle_auto_assignment(
        self,
        project: dict,
        best_assignee: dict | None,
    ):

        if not best_assignee:
            return

        self.automation_notifications.create_automation_activity(

            project_id=
                project["id"],

            activity_type=
                "AI_AUTO_ASSIGNMENT",

            title=
                "AI ביצע שיוך אוטומטי",

            description=
                (
                    f"הפעולה הוקצתה ל- "
                    f"{best_assignee.get('full_name')}"
                ),
        )

        self.automation_notifications.notification_service.create_notification(

            profile_id=
                best_assignee["id"],

            title=
                "AI הקצה לך פעולה חדשה",

            message=
                (
                    f"AI יצר והקצה לך "
                    f"פעולה חדשה בפרויקט "
                    f"{project['project_name']}"
                ),

            notification_type=
                "AI_AUTO_ASSIGNMENT",
        )

        print(

            "[AI_AUTOMATION] "

            f"Action assigned to: "
            f"{best_assignee.get('full_name')}"
        )

    # ==========================================
    # LOG AI ASSIGNMENT DECISION
    # ==========================================

    def log_ai_assignment_decision(
        self,
        project: dict,
        best_assignee: dict | None,
    ):

        if not best_assignee:

            self.log_ai_execution(

                project_id=
                    project["id"],

                execution_type=
                    "AI_ASSIGNMENT_DECISION",

                status=
                    "SKIPPED",

                details={
                    "decision":
                        "NO_ASSIGNEE",

                    "reason":
                        "no_best_assignee_found",
                },
            )

            return

        self.log_ai_execution(

            project_id=
                project["id"],

            execution_type=
                "AI_ASSIGNMENT_DECISION",

            status=
                "SUCCESS",

            details={
                "decision":
                    "ASSIGN",

                "assigned_to":
                    best_assignee.get(
                        "id"
                    ),

                "assigned_to_name":
                    best_assignee.get(
                        "full_name"
                    ),
            },
        )

    # ==========================================
    # LOG AI EXECUTION
    # ==========================================

    def log_ai_execution(
        self,
        execution_type: str,
        status: str,
        project_id: str | None = None,
        confidence: dict | None = None,
        details: dict | None = None,
        error: Exception | None = None,
    ):

        failure_classification = None

        if status == "FAILED":

            failure_error = (
                error
                or Exception(
                    (
                        details
                        or {}
                    ).get(
                        "error",
                        "Unknown AI execution failure"
                    )
                )
            )

            failure_classification = (
                self.ai_failure_classification_service
                .classify_failure(
                    failure_error
                )
            )

        log = AIExecutionLog(

            id=str(uuid4()),

            project_id=
                project_id,

            execution_type=
                execution_type,

            status=
                status,

            confidence_score=
                (
                    confidence.get("score")
                    if confidence
                    else None
                ),

            confidence_level=
                (
                    confidence.get(
                        "confidence_level"
                    )
                    if confidence
                    else None
                ),

            details=
                details,

            failure_type=
                (
                    failure_classification
                    or {}
                ).get(
                    "failure_type"
                ),

            severity=
                (
                    failure_classification
                    or {}
                ).get(
                    "severity"
                ),

            replayable=
                (
                    (
                        failure_classification
                        or {}
                    ).get(
                        "replayable"
                    )
                    if failure_classification
                    else True
                ),
        )

        self.execution_log_repository.create_log(
            log
        )

    # ==========================================
    # GENERATE RISK FINGERPRINT
    # ==========================================

    def generate_risk_fingerprint(
        self,
        project: dict,
        health: dict,
        risk_analysis: dict,
    ):

        raw = (

            f"{project.get('id')}|"

            f"{health.get('status')}|"

            f"{health.get('score')}|"

            f"{risk_analysis.get('risk_level')}"
        )

        return sha256(
            raw.encode()
        ).hexdigest()
