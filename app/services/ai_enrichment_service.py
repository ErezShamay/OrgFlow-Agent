from app.ai.ai_client import (
    AIClient
)

from app.config.ai_config import (
    DEFAULT_AI_MODEL
)

from app.prompts.prompt_loader import (
    PromptLoader
)

from app.schemas.ai_interpretation import (
    AIInterpretation
)


class AIEnrichmentService:

    def __init__(
        self,
        model_name: str | None = None
    ):

        self.model_name = (
            model_name
            or DEFAULT_AI_MODEL
        )

    def enrich_finding(
        self,
        finding
    ) -> AIInterpretation:

        prompt = (
            PromptLoader
            .load_prompt(

                "finding_enrichment",

                finding_type=
                    finding.finding_type,

                summary=
                    finding.summary,
            )
        )

        print(
            f"\nUSING MODEL: {self.model_name}\n"
        )

        content = (
            AIClient()
            .generate(
                prompt,
                prompt_name=
                "finding_enrichment",
            )
        )

        print(
            "\n=== RAW LLM RESPONSE ===\n"
        )

        print(content)

        print()

        return (
            AIInterpretation
            .from_ai_response(

                finding_id=
                    finding.id,

                model_name=
                    self.model_name,

                raw_response=
                    content,
            )
        )