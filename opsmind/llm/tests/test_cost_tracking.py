from __future__ import annotations

from opsmind.llm.config import LLMSettings
from opsmind.llm.cost import CostEstimator


def test_cost_tracking() -> None:
    settings = LLMSettings()
    estimator = CostEstimator(settings)
    cost = estimator.estimate_cost_usd("openai", "gpt-4o-mini", input_tokens=1000, output_tokens=1000)
    assert cost > 0
    assert round(cost, 6) == 0.00075
