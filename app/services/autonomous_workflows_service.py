from __future__ import annotations

AUTONOMOUS_WORKFLOWS_CONFIG = {
    "engine_id": "orgflow_autonomous_v1",
    "max_concurrent_runs": 5,
    "human_approval_gate": True,
    "supported_triggers": ["schedule", "event", "threshold"],
}


class AutonomousWorkflowsService:
    def get_config(self) -> dict:
        return AUTONOMOUS_WORKFLOWS_CONFIG

    def list_workflow_templates(self) -> dict:
        templates = [
            {"id": "escalation_response", "title": "Escalation auto-response"},
            {"id": "report_triage", "title": "Report triage pipeline"},
            {"id": "kpi_watchdog", "title": "KPI threshold watchdog"},
        ]
        return {"templates": templates, "total": len(templates)}

    def evaluate_run(self, *, template_id: str = "escalation_response", approved: bool = True) -> dict:
        return {
            "template_id": template_id,
            "started": approved,
            "requires_approval": AUTONOMOUS_WORKFLOWS_CONFIG["human_approval_gate"] and not approved,
        }

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "templates_defined": self.list_workflow_templates()["total"] >= 3,
        }
