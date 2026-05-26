from app.ai.settings import (
    AI_PROVIDER
)

from app.ai.providers.ollama_provider import (
    OllamaProvider
)


class AIGateway:

    @staticmethod
    def analyze_report(
        report_text: str
    ):

        if AI_PROVIDER == "ollama":

            return (
                OllamaProvider
                .analyze_report(
                    report_text
                )
            )

        raise Exception(
            f"Unsupported AI provider: {AI_PROVIDER}"
        )