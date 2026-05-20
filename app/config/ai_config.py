import os


DEFAULT_AI_MODEL = (
    os.getenv(
        "DEFAULT_AI_MODEL",
        "mistral"
    )
)