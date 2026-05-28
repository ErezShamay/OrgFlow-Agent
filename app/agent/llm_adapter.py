import json

from app.agent.intent_detector import IntentDetector
from app.config.settings import settings


class LLMAdapter:
    def __init__(self):
        self.mode = settings.ORG_FLOW_LLM_MODE
        self.model = settings.OPENAI_MODEL

    def classify_intent(self, user_request: str):
        if self._should_use_openai():
            return self._classify_intent_with_openai(user_request)

        return self._classify_intent_with_mock(user_request)

    def extract_entities(self, user_request: str):
        if self._should_use_openai():
            return self._extract_entities_with_openai(user_request)

        return self._extract_entities_with_mock(user_request)

    def generate_summary(self, context: dict):
        return {
            "status": "NOT_IMPLEMENTED"
        }

    def _should_use_openai(self) -> bool:
        return (
            self.mode == "openai"
            and bool(settings.get_active_openai_api_key())
        )

    def _classify_intent_with_mock(self, user_request: str):
        normalized = user_request.lower()

        if "דוח" in normalized:
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

    def _extract_entities_with_mock(self, user_request: str):
        known_projects = [
            "מגדלי הצפון",
            "גני השרון",
            "פארק הים"
        ]

        for project_name in known_projects:
            if project_name in user_request:
                return {
                    "status": "SUCCESS",
                    "entities": {
                        "project_name": project_name
                    },
                    "source": "LLM_MOCK"
                }

        if "מגדלי צפון" in user_request:
            return {
                "status": "SUCCESS",
                "entities": {
                    "project_name": "מגדלי צפון"
                },
                "source": "LLM_MOCK"
            }

        return {
            "status": "FAILED",
            "entities": {},
            "source": "LLM_MOCK"
        }

    def _classify_intent_with_openai(self, user_request: str):
        try:
            from openai import OpenAI

            client = OpenAI(api_key=settings.get_active_openai_api_key())

            prompt = f"""
            Return only valid JSON.

            Classify this Hebrew user request into one or more intents.

            Supported intents:
            - CHECK_MISSING_REPORTS
            - SEND_REMINDERS
            - SUMMARIZE_PROJECT_STATUS
            - FIND_REPORT
            - UNKNOWN

            User request:
            {user_request}

            JSON schema:
            {{
            "intents": ["..."],
            "confidence": 0.0,
            "source": "OPENAI"
            }}
            """

            response = client.responses.create(
                model=self.model,
                input=prompt
            )

            data = json.loads(response.output_text)
            data["source"] = "OPENAI"
            return data

        except Exception:
            return self._classify_intent_with_mock(user_request)

    def _extract_entities_with_openai(self, user_request: str):
        try:
            from openai import OpenAI

            client = OpenAI(api_key=settings.get_active_openai_api_key())

            prompt = f"""
            Return only valid JSON.

            Extract entities from this Hebrew user request.

            Supported entities:
            - project_name

            User request:
            {user_request}

            JSON schema:
            {{
            "status": "SUCCESS or FAILED",
            "entities": {{
                "project_name": "..."
            }},
            "source": "OPENAI"
            }}
            """

            response = client.responses.create(
                model=self.model,
                input=prompt
            )

            data = json.loads(response.output_text)
            data["source"] = "OPENAI"
            return data

        except Exception:
            return self._extract_entities_with_mock(user_request)