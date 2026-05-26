import time
from pydantic import BaseModel

from app.config.ai_config import (
    AI_PROVIDER,
    DEFAULT_AI_MODEL,
    AI_MAX_RETRIES,
)

from app.ai.providers.ollama_provider import (
    OllamaProvider
)

from app.repositories.ai_log_repository import (
    AILogRepository
)


class AIClient:

    def __init__(self):

        self.provider = (
            self._resolve_provider()
        )

    def _resolve_provider(self):

        if AI_PROVIDER == "ollama":

            return OllamaProvider()

        raise Exception(
            f"Unsupported AI provider: {AI_PROVIDER}"
        )

    def generate(
        self,
        prompt: str,
        prompt_name: str | None = None,
    ) -> str:

        last_error = None

        for attempt in range(
            AI_MAX_RETRIES + 1
        ):

            started_at = (
                time.time()
            )

            try:

                response = (
                    self.provider
                    .generate(prompt)
                )

                duration_ms = int(
                    (
                        time.time()
                        - started_at
                    ) * 1000
                )

                AILogRepository.create_log({

                    "provider":
                        AI_PROVIDER,

                    "model_name":
                        DEFAULT_AI_MODEL,

                    "prompt_name":
                        prompt_name,

                    "prompt":
                        prompt,

                    "response":
                        response,

                    "success":
                        True,

                    "duration_ms":
                        duration_ms,
                })

                return response

            except Exception as e:

                last_error = e

                duration_ms = int(
                    (
                        time.time()
                        - started_at
                    ) * 1000
                )

                AILogRepository.create_log({

                    "provider":
                        AI_PROVIDER,

                    "model_name":
                        DEFAULT_AI_MODEL,

                    "prompt_name":
                        prompt_name,

                    "prompt":
                        prompt,

                    "response":
                        None,

                    "success":
                        False,

                    "error_message":
                        str(e),

                    "duration_ms":
                        duration_ms,
                })

        raise last_error
    
        def generate_structured(
        self,
        prompt: str,
        schema,
        prompt_name: str | None = None,
        **kwargs,
    ):

        raw_response = (
            self.generate(
                prompt=prompt,
                prompt_name=prompt_name,
            )
        )

        return schema.from_ai_response(
            raw_response=raw_response,
            **kwargs,
        )