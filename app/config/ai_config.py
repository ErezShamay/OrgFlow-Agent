import os

AI_PROVIDER = (
    os.getenv(
        "AI_PROVIDER",
        "ollama"
    )
)

DEFAULT_AI_MODEL = (
    os.getenv(
        "DEFAULT_AI_MODEL",
        "mistral"
    )
)

AI_MAX_RETRIES = int(
    os.getenv(
        "AI_MAX_RETRIES",
        "2"
    )
)