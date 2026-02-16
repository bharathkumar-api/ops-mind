from __future__ import annotations

from opsmind.llm.config import LLMSettings
from opsmind.llm.cost import CostEstimator
from opsmind.llm.errors import AuthError, BadRequestError, ProviderUnavailableError, RateLimitError, TimeoutError
from opsmind.llm.providers.openai_provider import OpenAIProvider


def test_error_mapping_common_cases() -> None:
    provider = OpenAIProvider(LLMSettings(openai_api_key="x"), CostEstimator(LLMSettings(openai_api_key="x")))

    assert isinstance(provider.map_exception(Exception("Unauthorized")), AuthError)
    assert isinstance(provider.map_exception(Exception("429 too many requests")), RateLimitError)
    assert isinstance(provider.map_exception(Exception("Request timeout")), TimeoutError)
    assert isinstance(provider.map_exception(Exception("invalid schema")), BadRequestError)
    assert isinstance(provider.map_exception(Exception("upstream crash")), ProviderUnavailableError)
