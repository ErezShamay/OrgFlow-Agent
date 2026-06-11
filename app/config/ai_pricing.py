from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelPricing:
    input_cost_per_1k_tokens: float
    output_cost_per_1k_tokens: float


# Estimated provider pricing (USD per 1K tokens). Update when models change.
MODEL_PRICING: dict[str, ModelPricing] = {
    "gpt-4o-mini": ModelPricing(0.00015, 0.0006),
    "gpt-4o": ModelPricing(0.0025, 0.01),
    "gpt-4.1-mini": ModelPricing(0.0004, 0.0016),
    "gpt-4.1": ModelPricing(0.002, 0.008),
    "claude-3-5-sonnet-latest": ModelPricing(0.003, 0.015),
    "gemini-2.0-flash": ModelPricing(0.0001, 0.0004),
    "cache": ModelPricing(0.0, 0.0),
    "review-audit": ModelPricing(0.0, 0.0),
}


def resolve_model_pricing(model_name: str | None) -> ModelPricing:
    normalized = (model_name or "").strip().lower()
    if not normalized:
        return ModelPricing(0.0, 0.0)

    if normalized in MODEL_PRICING:
        return MODEL_PRICING[normalized]

    for key, pricing in MODEL_PRICING.items():
        if key in normalized:
            return pricing

    return ModelPricing(0.0, 0.0)
