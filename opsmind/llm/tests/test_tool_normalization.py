from __future__ import annotations

from opsmind.llm.config import LLMSettings
from opsmind.llm.cost import CostEstimator
from opsmind.llm.providers.anthropic_provider import AnthropicProvider
from opsmind.llm.providers.gemini_provider import GeminiProvider
from opsmind.llm.providers.openai_provider import OpenAIProvider


def _settings() -> LLMSettings:
    return LLMSettings(openai_api_key="x", anthropic_api_key="y", google_api_key="z")


def test_openai_tool_normalization() -> None:
    provider = OpenAIProvider(_settings(), CostEstimator(_settings()))
    out = provider._normalize_tool_calls(
        [{"id": "abc", "function": {"name": "lookup", "arguments": '{"id": 1}'}}]
    )
    assert out[0].id == "abc"
    assert out[0].name == "lookup"
    assert out[0].arguments == {"id": 1}


def test_anthropic_tool_normalization() -> None:
    provider = AnthropicProvider(_settings(), CostEstimator(_settings()))
    out = provider._normalize_tool_calls([{"type": "tool_use", "id": "t1", "name": "lookup", "input": {"id": 2}}])
    assert out[0].id == "t1"
    assert out[0].arguments == {"id": 2}


def test_gemini_tool_normalization() -> None:
    provider = GeminiProvider(_settings(), CostEstimator(_settings()))
    out = provider._normalize_tool_calls([{"functionCall": {"name": "lookup", "args": {"id": 3}}}])
    assert out[0].name == "lookup"
    assert out[0].arguments == {"id": 3}
    assert out[0].id.startswith("gemini_tool_")
