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


class AnthropicProvider(LLMProvider):
    name = "anthropic"
    supports_tools = True
    supports_streaming = True
    supports_vision = True

    def __init__(self, settings: LLMSettings, cost_estimator: CostEstimator) -> None:
        self.settings = settings
        self.cost_estimator = cost_estimator
        self.api_key = settings.anthropic_api_key

    def _resolve_model(self, logical_model: str) -> str:
        return self.settings.model_mapping[self.name].get(logical_model, logical_model)

    async def generate(self, req: LLMRequest) -> LLMResponse:
        if not self.api_key:
            raise ProviderUnavailableError("ANTHROPIC_API_KEY is not configured", provider=self.name)

        started = time.perf_counter()
        provider_model = self._resolve_model(req.model)
        payload: dict[str, Any] = {
            "model": provider_model,
            "max_tokens": req.max_output_tokens or 1024,
            "messages": [{"role": m.role, "content": self.message_to_text(m)} for m in req.messages if m.role != "system"],
            "system": "\n".join(self.message_to_text(m) for m in req.messages if m.role == "system"),
            "temperature": req.temperature,
            "top_p": req.top_p,
        }
        if req.tools:
            payload["tools"] = [
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.json_schema,
                    "metadata": {"version": t.version},
                }
                for t in req.tools
            ]
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        try:
            resp = await asyncio.to_thread(requests.post, "https://api.anthropic.com/v1/messages" , json=payload, headers=headers, timeout=self.settings.request_timeout_ms / 1000)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:  # noqa: BLE001
            raise self.map_exception(exc) from exc

        latency_ms = int((time.perf_counter() - started) * 1000)
        text_blocks = [block.get("text", "") for block in data.get("content", []) if block.get("type") == "text"]
        tool_calls = self._normalize_tool_calls(data.get("content", []))
        usage = self._usage_from_payload(data.get("usage", {}), latency_ms, provider_model)
        return LLMResponse(
            request_id=req.request_id,
            provider=self.name,
            provider_model=provider_model,
            output_text="".join(text_blocks),
            tool_calls=tool_calls,
            usage=usage,
            finish_reason=data.get("stop_reason", "stop"),
            raw=data if self.settings.llm_debug_raw_responses else None,
        )

    async def stream(self, req: LLMRequest):
        raise ProviderUnavailableError("Streaming is not implemented in this build", provider=self.name)

    def _normalize_tool_calls(self, content_blocks: list[dict[str, Any]]) -> list[ToolCall]:
        calls: list[ToolCall] = []
        for block in content_blocks:
            if block.get("type") != "tool_use":
                continue
            name = block.get("name", "unknown")
            args = block.get("input") if isinstance(block.get("input"), dict) else {}
            call_id = block.get("id") or self.stable_tool_call_id(name, args, fallback="anthropic_tool")
            calls.append(ToolCall(id=call_id, name=name, arguments=args))
        return calls

    def _usage_from_payload(self, payload: dict[str, Any], latency_ms: int, provider_model: str) -> Usage:
        input_tokens = int(payload.get("input_tokens", 0))
        output_tokens = int(payload.get("output_tokens", 0))
        return Usage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            estimated_cost_usd=self.cost_estimator.estimate_cost_usd(
                self.name, provider_model, input_tokens, output_tokens
            ),
            latency_ms=latency_ms,
        )
