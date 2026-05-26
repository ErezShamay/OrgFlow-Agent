from app.prompts.prompt_loader import (
    PromptLoader
)

from app.schemas.ai_interpretation import (
    AIInterpretation
)

from app.ai.workflows.base_ai_workflow import (
    BaseAIWorkflow
)


class FindingEnrichmentWorkflow(
    BaseAIWorkflow
):

    def build_prompt(
        self,
        finding,
    ) -> str:

        return (
            PromptLoader
            .load_prompt(

                "finding_enrichment",

                finding_type=
                    finding.finding_type,

                summary=
                    finding.summary,
            )
        )

    def execute(
        self,
        finding,
        model_name: str,
    ) -> AIInterpretation:

        prompt = (
            self.build_prompt(
                finding
            )
        )

        return (
            self.client
            .generate_structured(

                prompt=
                    prompt,

                schema=
                    AIInterpretation,

                prompt_name=
                    "finding_enrichment",

                finding_id=
                    finding.id,

                model_name=
                    model_name,
            )
        )