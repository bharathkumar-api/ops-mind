from __future__ import annotations

import asyncio

from opsmind.llm.config import LLMSettings
from opsmind.llm.errors import RateLimitError
from opsmind.llm.provider_base import LLMProvider
from opsmind.llm.router import LLMRouter
from opsmind.llm.types import LLMRequest, LLMResponse, Message, Usage


class DummyProvider(LLMProvider):
    supports_streaming = False

    def __init__(self, name: str, fail: bool = False) -> None:
        self.name = name
        self.fail = fail

    async def generate(self, req: LLMRequest) -> LLMResponse:
        if self.fail:
            raise RateLimitError("ratelimited", provider=self.name)
        return LLMResponse(
            request_id=req.request_id,
            provider=self.name,
            provider_model=f"{self.name}-fast",
            output_text=f"ok-{self.name}",
            tool_calls=[],
            usage=Usage(input_tokens=10, output_tokens=10, total_tokens=20, estimated_cost_usd=0.01, latency_ms=12),
            finish_reason="stop",
        )


def test_router_chooses_default_provider() -> None:
    settings = LLMSettings(llm_providers_enabled=["openai", "anthropic"], llm_default_provider="anthropic")
    router = LLMRouter(settings=settings, providers={"openai": DummyProvider("openai"), "anthropic": DummyProvider("anthropic")})

    req = LLMRequest(request_id="r1", model="fast", messages=[Message(role="user", content="hello")])
    res = asyncio.run(router.generate(req))
    assert res.provider == "anthropic"


def test_router_fallback_on_retryable_error() -> None:
    settings = LLMSettings(llm_providers_enabled=["openai", "anthropic"], llm_default_provider="openai")
    router = LLMRouter(
        settings=settings,
        providers={"openai": DummyProvider("openai", fail=True), "anthropic": DummyProvider("anthropic")},
    )

    req = LLMRequest(request_id="r2", model="fast", messages=[Message(role="user", content="hello")])
    res = asyncio.run(router.generate(req))
    assert res.provider == "anthropic"
