from __future__ import annotations

import time
from typing import Any

import asyncio
import requests

from ..config import LLMSettings
from ..cost import CostEstimator
from ..errors import ProviderUnavailableError
from ..provider_base import LLMProvider
from ..types import LLMRequest, LLMResponse, ToolCall, Usage


class OpenAIProvider(LLMProvider):
    name = "openai"
    supports_tools = True
    supports_streaming = True
    supports_vision = True

    def __init__(self, settings: LLMSettings, cost_estimator: CostEstimator) -> None:
        self.settings = settings
        self.cost_estimator = cost_estimator
        self.api_key = settings.openai_api_key

    def _resolve_model(self, logical_model: str) -> str:
        return self.settings.model_mapping[self.name].get(logical_model, logical_model)

    async def generate(self, req: LLMRequest) -> LLMResponse:
        if not self.api_key:
            raise ProviderUnavailableError("OPENAI_API_KEY is not configured", provider=self.name)
        started = time.perf_counter()
        provider_model = self._resolve_model(req.model)
        payload: dict[str, Any] = {
            "model": provider_model,
            "messages": [
                {"role": m.role, "content": self.message_to_text(m), **({"name": m.name} if m.name else {})}
                for m in req.messages
            ],
            "temperature": req.temperature,
            "top_p": req.top_p,
            "max_tokens": req.max_output_tokens,
        }
        if req.tools:
            payload["tools"] = [self.tool_spec_to_openai(t) for t in req.tools]
            if req.tool_choice:
                payload["tool_choice"] = req.tool_choice

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        try:
            resp = await asyncio.to_thread(requests.post, "https://api.openai.com/v1/chat/completions" , json=payload, headers=headers, timeout=self.settings.request_timeout_ms / 1000)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:  # noqa: BLE001
            raise self.map_exception(exc) from exc

        latency_ms = int((time.perf_counter() - started) * 1000)
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        tool_calls = self._normalize_tool_calls(message.get("tool_calls", []))
        usage = self._usage_from_payload(data.get("usage", {}), latency_ms, provider_model)
        return LLMResponse(
            request_id=req.request_id,
            provider=self.name,
            provider_model=provider_model,
            output_text=message.get("content") or "",
            tool_calls=tool_calls,
            usage=usage,
            finish_reason=choice.get("finish_reason", "stop"),
            raw=data if self.settings.llm_debug_raw_responses else None,
        )

    async def stream(self, req: LLMRequest):
        raise ProviderUnavailableError("Streaming is not implemented in this build", provider=self.name)

    def _usage_from_payload(self, payload: dict[str, Any], latency_ms: int, provider_model: str) -> Usage:
        input_tokens = int(payload.get("prompt_tokens", 0))
        output_tokens = int(payload.get("completion_tokens", 0))
        total = int(payload.get("total_tokens", input_tokens + output_tokens))
        return Usage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total,
            estimated_cost_usd=self.cost_estimator.estimate_cost_usd(
                self.name, provider_model, input_tokens, output_tokens
            ),
            latency_ms=latency_ms,
        )

    def _normalize_tool_calls(self, calls: list[dict[str, Any]]) -> list[ToolCall]:
        normalized: list[ToolCall] = []
        for call in calls:
            fn = call.get("function", {})
            name = fn.get("name") or "unknown"
            args = self.safe_parse_json(fn.get("arguments"))
            call_id = call.get("id") or self.stable_tool_call_id(name, args, fallback="openai_tool")
            normalized.append(ToolCall(id=call_id, name=name, arguments=args))
        return normalized
