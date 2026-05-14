import uuid

from app.agent.intent_detector import IntentDetector


class Planner:
    def build_plan(self, intents: list[str]) -> dict:
        steps = []

        if IntentDetector.CHECK_MISSING_REPORTS in intents:
            steps.append({
                "step_id": str(uuid.uuid4()),
                "step_type": "CHECK_MISSING_REPORTS"
            })

        if IntentDetector.SEND_REMINDERS in intents:
            steps.append({
                "step_id": str(uuid.uuid4()),
                "step_type": "SEND_REMINDERS"
            })

        if IntentDetector.SUMMARIZE_PROJECT_STATUS in intents:
            steps.append({
                "step_id": str(uuid.uuid4()),
                "step_type": "SUMMARIZE_PROJECT_STATUS"
            })

        if IntentDetector.FIND_REPORT in intents:
            steps.append({
                "step_id": str(uuid.uuid4()),
                "step_type": "FIND_REPORT"
            })

        return {
            "plan_id": str(uuid.uuid4()),
            "steps": steps
        }