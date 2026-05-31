from app.repositories.operational_action_repository import (
    OperationalActionRepository
)

from app.constants.action_statuses import (
    OPEN,
    IN_PROGRESS,
    BLOCKED,
    ESCALATED,
    COMPLETED,
)

from app.repositories.workspace_activity_repository import (
    WorkspaceActivityRepository,
)


class OperationalActionService:

    def __init__(self):

        self.repository = (
            OperationalActionRepository()
        )
        self._action_attachments: dict[str, list[dict]] = {}
        self._action_notifications: dict[str, list[dict]] = {}
        self._action_history: dict[str, list[dict]] = {}
        self._recurring_actions: dict[str, list[dict]] = {}
        self._action_templates: dict[str, list[dict]] = {}

    # ==========================================
    # GETTERS
    # ==========================================

    def get_open_actions(
        self
    ):

        return (
            self.repository
            .get_open_actions()
        )

    def get_action_details(
        self,
        action_id: str,
    ):

        action = (
            self.repository
            .get_action_by_id(
                action_id
            )
        )

        if not action:

            return {
                "success": False,
                "message": "Action not found",
            }

        activities = (
            WorkspaceActivityRepository
            .get_project_activity(
                action["project_id"]
            )
        )

        related_activities = []

        for activity in activities:

            description = (
                activity.get(
                    "description"
                )
                or ""
            )

            if (
                action["title"]
                in description
            ):

                related_activities.append(
                    activity
                )

        return {

            "success": True,

            "action":
                action,

            "timeline":
                related_activities,

            "sla": {

                "due_date":
                    action.get(
                        "due_date"
                    ),

                "is_overdue":
                    action.get(
                        "status"
                    )
                    != COMPLETED
                    and bool(
                        action.get(
                            "due_date"
                        )
                    ),
            },

            "assignment": {

                "assigned_to":
                    action.get(
                        "assigned_to"
                    ),
            },
        }

    def get_escalations(
        self
    ):

        actions = (
            self.repository
            .get_open_actions()
        )

        escalations = []

        for action in actions:

            if (
                action[
                    "action_type"
                ]
                == "ESCALATION"
            ):

                escalations.append(
                    action
                )

        return escalations

    # ==========================================
    # STATUS MANAGEMENT
    # ==========================================

    def update_status(
        self,
        action_id: str,
        status: str,
    ):

        action = (
            self.repository
            .update_action_status(
                action_id,
                status,
            )
        )

        WorkspaceActivityRepository.create_activity(

            project_id=
                action["project_id"],

            activity_type=
                "ACTION_STATUS_CHANGED",

            title=
                "סטטוס פעולה עודכן",

            description=
                f"{action['title']} → {status}",
        )
        self._append_history(
            action_id=action_id,
            event_type="STATUS_CHANGED",
            payload={"status": status},
        )

        return action

    def start_action(
        self,
        action_id: str,
    ):

        return (
            self.update_status(
                action_id,
                IN_PROGRESS,
            )
        )

    def block_action(
        self,
        action_id: str,
    ):

        return (
            self.update_status(
                action_id,
                BLOCKED,
            )
        )

    def complete_action(
        self,
        action_id: str,
    ):

        return (
            self.update_status(
                action_id,
                COMPLETED,
            )
        )

    def escalate_action(
        self,
        action_id: str,
    ):

        return (
            self.update_status(
                action_id,
                ESCALATED,
            )
        )

    def close_action(
        self,
        action_id: str,
    ):

        action = (
            self.repository
            .close_action(
                action_id
            )
        )

        WorkspaceActivityRepository.create_activity(
            project_id=
                action["project_id"],
            activity_type=
                "ACTION_STATUS_CHANGED",
            title=
                "פעולה נסגרה",
            description=
                f"{action['title']} → CLOSED",
        )
        self._append_history(
            action_id=action_id,
            event_type="STATUS_CHANGED",
            payload={"status": "CLOSED"},
        )

        return action

    def assign_action(
        self,
        action_id: str,
        assigned_to: str,
    ):

        action = (
            self.repository
            .assign_action(

                action_id=
                    action_id,

                assigned_to=
                    assigned_to,
            )
        )

        WorkspaceActivityRepository.create_activity(

            project_id=
                action["project_id"],

            activity_type=
                "ACTION_ASSIGNED",

            title=
                "פעולה שויכה",

            description=
                f"{action['title']} → {assigned_to}",
        )
        self._append_history(
            action_id=action_id,
            event_type="ASSIGNED",
            payload={"assigned_to": assigned_to},
        )

        return action

    # ==========================================
    # BACKLOG CAPABILITIES
    # ==========================================

    def get_action_priorities(self, project_id: str):
        actions = self.repository.get_open_actions_by_project(project_id)
        ranked = []
        for action in actions:
            action_type = (action.get("action_type") or "").upper()
            priority_score = 50
            if action_type == "ESCALATION":
                priority_score = 90
            elif action_type in {"FOLLOW_UP", "RETRY"}:
                priority_score = 70
            ranked.append(
                {
                    **action,
                    "priority_score": priority_score,
                    "priority": "HIGH" if priority_score >= 80 else "MEDIUM",
                }
            )
        ranked.sort(
            key=lambda item: (
                -item["priority_score"],
                str(item.get("due_date") or ""),
            )
        )
        return {
            "project_id": project_id,
            "total_actions": len(ranked),
            "actions": ranked,
        }

    def get_dependency_graph(self, project_id: str):
        actions = self.repository.get_open_actions_by_project(project_id)
        nodes = [{"id": row["id"], "label": row.get("title")} for row in actions]
        edges = []
        for row in actions:
            blocked_by = row.get("blocked_by") or []
            for dependency in blocked_by:
                edges.append(
                    {"source": dependency, "target": row["id"], "type": "BLOCKS"}
                )
        return {
            "project_id": project_id,
            "nodes": nodes,
            "edges": edges,
            "total_nodes": len(nodes),
            "total_edges": len(edges),
        }

    def create_recurring_action(self, project_id: str, title: str, recurrence_rule: str, created_by: str):
        payload = {
            "id": f"rec-{len(self._recurring_actions.get(project_id, [])) + 1}",
            "project_id": project_id,
            "title": title,
            "recurrence_rule": recurrence_rule,
            "created_by": created_by,
            "status": OPEN,
        }
        self._recurring_actions.setdefault(project_id, []).append(payload)
        return payload

    def list_recurring_actions(self, project_id: str):
        recurring = self._recurring_actions.get(project_id, [])
        return {
            "project_id": project_id,
            "total_recurring_actions": len(recurring),
            "items": recurring,
        }

    def bulk_create_actions(self, project_id: str, actions: list[dict]):
        created = []
        for idx, payload in enumerate(actions, start=1):
            created.append(
                {
                    "id": f"bulk-{idx}",
                    "project_id": project_id,
                    "title": payload.get("title", f"Action {idx}"),
                    "action_type": payload.get("action_type", "GENERAL"),
                    "status": payload.get("status", OPEN),
                }
            )
        return {
            "project_id": project_id,
            "created_count": len(created),
            "actions": created,
        }

    def add_attachment(self, action_id: str, filename: str, uploaded_by: str):
        attachment = {
            "id": f"att-{len(self._action_attachments.get(action_id, [])) + 1}",
            "action_id": action_id,
            "filename": filename,
            "uploaded_by": uploaded_by,
        }
        self._action_attachments.setdefault(action_id, []).append(attachment)
        self._append_history(action_id, "ATTACHMENT_ADDED", {"filename": filename})
        return attachment

    def list_attachments(self, action_id: str):
        return self._action_attachments.get(action_id, [])

    def delete_attachment(self, action_id: str, attachment_id: str):
        current = self._action_attachments.get(action_id, [])
        remaining = [item for item in current if item["id"] != attachment_id]
        if len(remaining) == len(current):
            return False
        self._action_attachments[action_id] = remaining
        self._append_history(action_id, "ATTACHMENT_DELETED", {"attachment_id": attachment_id})
        return True

    def create_notification(self, action_id: str, recipient_id: str, message: str, channel: str = "IN_APP"):
        notification = {
            "id": f"not-{len(self._action_notifications.get(action_id, [])) + 1}",
            "action_id": action_id,
            "recipient_id": recipient_id,
            "message": message,
            "channel": channel,
        }
        self._action_notifications.setdefault(action_id, []).append(notification)
        return notification

    def list_notifications(self, action_id: str):
        return self._action_notifications.get(action_id, [])

    def get_action_analytics(self, project_id: str):
        actions = self.repository.get_open_actions_by_project(project_id)
        return {
            "project_id": project_id,
            "total_open_actions": len(actions),
            "escalated_actions": len(
                [row for row in actions if row.get("status") == ESCALATED]
            ),
            "blocked_actions": len(
                [row for row in actions if row.get("status") == BLOCKED]
            ),
        }

    def add_comment(self, action_id: str, comment: str, created_by: str):
        item = {
            "id": f"c-{len(self._action_history.get(action_id, [])) + 1}",
            "action_id": action_id,
            "comment": comment,
            "created_by": created_by,
        }
        self._append_history(
            action_id=action_id,
            event_type="COMMENT_ADDED",
            payload=item,
        )
        return item

    def list_comments(self, action_id: str):
        events = self._action_history.get(action_id, [])
        return [
            event["payload"]
            for event in events
            if event.get("event_type") == "COMMENT_ADDED"
        ]

    def get_history(self, action_id: str):
        return self._action_history.get(action_id, [])

    def get_sla_dashboard(self, project_id: str):
        actions = self.repository.get_open_actions_by_project(project_id)
        breached = [row for row in actions if row.get("due_date")]
        return {
            "project_id": project_id,
            "tracked_actions": len(actions),
            "breached_actions": len(breached),
        }

    def retry_action(self, action_id: str, reason: str):
        action = self.update_status(action_id, IN_PROGRESS)
        self._append_history(
            action_id=action_id,
            event_type="RETRY_TRIGGERED",
            payload={"reason": reason},
        )
        return action

    def set_owner(self, action_id: str, owner_id: str):
        action = self.repository.assign_action(action_id, owner_id)
        self._append_history(
            action_id=action_id,
            event_type="OWNER_UPDATED",
            payload={"owner_id": owner_id},
        )
        return action

    def escalate_with_hierarchy(self, action_id: str, level: str, reason: str):
        action = self.update_status(action_id, ESCALATED)
        self._append_history(
            action_id=action_id,
            event_type="ESCALATION_LEVEL_SET",
            payload={"level": level, "reason": reason},
        )
        action["escalation_level"] = level
        return action

    def generate_ai_actions(self, project_id: str, context: str):
        suggestion = {
            "id": "ai-action-1",
            "project_id": project_id,
            "title": f"AI: {context[:40]}",
            "action_type": "FOLLOW_UP",
            "confidence": 0.78,
        }
        return {
            "project_id": project_id,
            "generated_actions": [suggestion],
        }

    def create_template(self, project_id: str, name: str, title: str, description: str, category: str):
        template = {
            "id": f"tpl-{len(self._action_templates.get(project_id, [])) + 1}",
            "project_id": project_id,
            "name": name,
            "title": title,
            "description": description,
            "category": category,
        }
        self._action_templates.setdefault(project_id, []).append(template)
        return template

    def list_templates(self, project_id: str):
        items = self._action_templates.get(project_id, [])
        return {
            "project_id": project_id,
            "total_templates": len(items),
            "templates": items,
        }

    def apply_template(self, project_id: str, template_id: str, created_by: str):
        templates = self._action_templates.get(project_id, [])
        template = next((item for item in templates if item["id"] == template_id), None)
        if not template:
            return None
        return {
            "id": f"applied-{template_id}",
            "project_id": project_id,
            "title": template["title"],
            "description": template["description"],
            "action_type": template["category"],
            "created_by": created_by,
            "status": OPEN,
        }

    def categorize_action(self, action_id: str, category: str):
        self._append_history(
            action_id=action_id,
            event_type="CATEGORY_UPDATED",
            payload={"category": category},
        )
        action = self.repository.get_action_by_id(action_id)
        if not action:
            return None
        action["category"] = category
        return action

    def _append_history(self, action_id: str, event_type: str, payload: dict):
        self._action_history.setdefault(action_id, []).append(
            {
                "event_type": event_type,
                "payload": payload,
            }
        )
