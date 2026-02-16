from __future__ import annotations

import asyncio
import statistics
import time
from collections import defaultdict, deque
from typing import AsyncIterator

from .cache import LLMCache
from .config import LLMSettings
from .cost import CostEstimator
from .errors import BudgetExceededError, OpsMindLLMError, ProviderUnavailableError
from .policies import PolicyEngine
from .provider_base import LLMProvider
from .providers.anthropic_provider import AnthropicProvider
from .providers.gemini_provider import GeminiProvider
from .providers.openai_provider import OpenAIProvider
from .telemetry import Telemetry
from .types import LLMRequest, LLMResponse, LLMResponseChunk


class LLMRouter:
    def __init__(
        self,
        settings: LLMSettings,
        providers: dict[str, LLMProvider] | None = None,
        policy_engine: PolicyEngine | None = None,
        telemetry: Telemetry | None = None,
        cache: LLMCache | None = None,
    ) -> None:
        self.settings = settings
        self.cost_estimator = CostEstimator(settings)
        self.providers = providers or {
            "openai": OpenAIProvider(settings, self.cost_estimator),
            "anthropic": AnthropicProvider(settings, self.cost_estimator),
            "gemini": GeminiProvider(settings, self.cost_estimator),
        }
        self.policy_engine = policy_engine or PolicyEngine()
        self.telemetry = telemetry or Telemetry(debug_raw=settings.llm_debug_raw_responses)
        self.cache = cache or LLMCache()
        self._latency_windows: dict[str, deque[int]] = defaultdict(lambda: deque(maxlen=50))

    def _provider_order(self, logical_model: str) -> list[str]:
        enabled = [p for p in self.settings.llm_providers_enabled if p in self.providers]
        if not enabled:
            raise ProviderUnavailableError("No providers are enabled")

        order = sorted(
            enabled,
            key=lambda p: (
                0 if p == self.settings.llm_default_provider else 1,
                self._latency_p95(p),
            ),
        )
        return [p for p in order if logical_model in self.settings.model_mapping.get(p, {}) or logical_model]

    def _latency_p95(self, provider: str) -> int:
        window = self._latency_windows.get(provider)
        if not window:
            return 0
        if len(window) < 2:
            return window[-1]
        p95 = statistics.quantiles(window, n=100)[94]
        return int(p95)

    def _should_skip_for_latency(self, provider: str) -> bool:
        threshold = self.settings.request_timeout_ms * 0.8
        return self._latency_p95(provider) > threshold

    def _enforce_budget_pre(self, req: LLMRequest) -> None:
        if req.max_output_tokens and req.max_output_tokens > self.settings.max_tokens_per_request:
            raise BudgetExceededError("Requested max_output_tokens exceeds policy")

    def _enforce_budget_post(self, res: LLMResponse) -> None:
        if res.usage.total_tokens > self.settings.max_tokens_per_request:
            raise BudgetExceededError("Response token usage exceeds policy", provider=res.provider)
        if res.usage.estimated_cost_usd > self.settings.max_cost_usd_per_request:
            raise BudgetExceededError("Response estimated cost exceeds policy", provider=res.provider)

    async def generate(self, req: LLMRequest) -> LLMResponse:
        req = self.policy_engine.enforce(req)
        self._enforce_budget_pre(req)

        logical_model = req.model
        fallbacks = 0
        last_error: OpsMindLLMError | None = None

        for provider_name in self._provider_order(logical_model):
            provider = self.providers[provider_name]
            if self._should_skip_for_latency(provider_name):
                continue

            provider_model = self.settings.model_mapping.get(provider_name, {}).get(req.model, req.model)
            if self.cache.is_cacheable(req):
                cached = self.cache.get(provider_name, provider_model, req)
                if cached:
                    return cached

            started = time.perf_counter()
            try:
                with self.telemetry.span("llm.generate", {"provider": provider_name}):
                    response = await asyncio.wait_for(
                        provider.generate(req), timeout=self.settings.request_timeout_ms / 1000
                    )
                latency_ms = int((time.perf_counter() - started) * 1000)
                self._latency_windows[provider_name].append(latency_ms)
                self._enforce_budget_post(response)
                if self.cache.is_cacheable(req):
                    self.cache.set(provider_name, provider_model, req, response)
                self.telemetry.emit_event(
                    request_id=req.request_id,
                    provider=response.provider,
                    provider_model=response.provider_model,
                    latency_ms=response.usage.latency_ms,
                    tokens=response.usage.total_tokens,
                    cost=response.usage.estimated_cost_usd,
                    outcome="success",
                    fallback_count=fallbacks,
                    prompt_chars=sum(len(str(m.content)) for m in req.messages),
                )
                return response
            except Exception as exc:  # noqa: BLE001
                mapped = provider.map_exception(exc)
                last_error = mapped
                fallbacks += 1
                self.telemetry.emit_event(
                    request_id=req.request_id,
                    provider=provider_name,
                    provider_model=provider_model,
                    latency_ms=int((time.perf_counter() - started) * 1000),
                    tokens=0,
                    cost=0,
                    outcome="error",
                    error_code=mapped.code,
                    fallback_count=fallbacks,
                )
                if not mapped.retryable:
                    raise mapped
                continue

        raise last_error or ProviderUnavailableError("No provider succeeded")

    async def stream(self, req: LLMRequest) -> AsyncIterator[LLMResponseChunk]:
        req = self.policy_engine.enforce(req)
        self._enforce_budget_pre(req)

        for provider_name in self._provider_order(req.model):
            provider = self.providers[provider_name]
            if not provider.supports_streaming:
                continue
            try:
                async for chunk in provider.stream(req):
                    yield chunk
                return
            except Exception as exc:  # noqa: BLE001
                mapped = provider.map_exception(exc)
                if not mapped.retryable:
                    raise mapped
                continue
        raise ProviderUnavailableError("No provider could stream this request")
