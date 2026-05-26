import os

AI_PROVIDER = os.getenv(
    "AI_PROVIDER",
    "ollama"
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "mistral"
)