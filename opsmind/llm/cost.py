from __future__ import annotations

from copy import deepcopy

from .config import LLMSettings

DEFAULT_PRICING: dict[str, dict[str, dict[str, float]]] = {
    "openai": {
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-4.1-mini": {"input": 0.0004, "output": 0.0016},
        "o3-mini": {"input": 0.0011, "output": 0.0044},
    },
    "anthropic": {
        "claude-3-5-haiku-latest": {"input": 0.00025, "output": 0.00125},
        "claude-3-5-sonnet-latest": {"input": 0.003, "output": 0.015},
        "claude-3-7-sonnet-latest": {"input": 0.003, "output": 0.015},
    },
    "gemini": {
        "gemini-2.0-flash": {"input": 0.0001, "output": 0.0004},
        "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
    },
}


class CostEstimator:
    def __init__(self, settings: LLMSettings) -> None:
        self._pricing = deepcopy(DEFAULT_PRICING)
        override = settings.pricing_override
        for provider, models in override.items():
            self._pricing.setdefault(provider, {}).update(models)

    def estimate_cost_usd(self, provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
        provider_prices = self._pricing.get(provider, {})
        model_price = provider_prices.get(model)
        if not model_price:
            return 0.0
        input_cost = (input_tokens / 1000) * model_price.get("input", 0.0)
        output_cost = (output_tokens / 1000) * model_price.get("output", 0.0)
        return round(input_cost + output_cost, 8)
