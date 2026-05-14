from app.agent.intent_detector import IntentDetector


class LLMAdapter:
    def classify_intent(self, user_request: str):
        normalized = user_request.lower()

        if "פרויקט" in normalized and "דוח" in normalized:
            return {
                "intents": [
                    IntentDetector.FIND_REPORT
                ],
                "confidence": 0.65,
                "source": "LLM_MOCK"
            }

        return {
            "intents": [
                IntentDetector.UNKNOWN
            ],
            "confidence": 0.10,
            "source": "LLM_MOCK"
        }

    def extract_entities(self, user_request: str):
        return {
            "status": "NOT_IMPLEMENTED"
        }

    def generate_summary(self, context: dict):
        return {
            "status": "NOT_IMPLEMENTED"
        }