import requests

from app.ai.settings import (
    OLLAMA_MODEL
)


class OllamaProvider:

    OLLAMA_URL = (
        "http://localhost:11434/api/generate"
    )

    @staticmethod
    def analyze_report(
        report_text: str
    ):

        prompt = f"""
You are an AI construction operations analyst.

Analyze the following weekly construction report.

Identify:
- operational risks
- delays
- tenant risks
- safety issues
- recommended actions

Return concise operational insights.

REPORT:

{report_text}
"""

        response = requests.post(

            OllamaProvider.OLLAMA_URL,

            json={
                "model":
                    OLLAMA_MODEL,

                "prompt":
                    prompt,

                "stream":
                    False,
            }
        )

        data = response.json()

        return data.get(
            "response",
            ""
        )