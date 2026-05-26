from pathlib import Path

from app.prompts.prompt_registry import (
    PROMPTS
)


class PromptLoader:

    PROMPTS_DIR = (
        Path(__file__)
        .parent
    )

    @staticmethod
    def load_prompt(
        prompt_name: str,
        **kwargs,
    ) -> str:

        if prompt_name not in PROMPTS:

            raise Exception(
                f"Unknown prompt: {prompt_name}"
            )

        prompt_file = (
            PROMPTS[prompt_name]["file"]
        )

        prompt_path = (
            PromptLoader.PROMPTS_DIR
            / f"{prompt_file}.txt"
        )

        prompt_template = (
            prompt_path
            .read_text(
                encoding="utf-8"
            )
        )

        return prompt_template.format(
            **kwargs
        )