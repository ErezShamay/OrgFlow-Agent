import ollama

from app.config.ai_config import (
    DEFAULT_AI_MODEL
)

from app.ai.providers.base_provider import (
    BaseProvider
)


class OllamaProvider(
    BaseProvider
):

    def __init__(
        self,
        model_name: str | None = None
    ):

        self.model_name = (
            model_name
            or DEFAULT_AI_MODEL
        )

    def generate(
        self,
        prompt: str,
    ) -> str:

        response = ollama.chat(

            model=self.model_name,

            messages=[
                {
                    "role": "user",

                    "content": prompt,
                }
            ]
        )

        return (
            response["message"]["content"]
        )