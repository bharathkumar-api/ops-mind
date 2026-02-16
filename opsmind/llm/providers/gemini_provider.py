from __future__ import annotations

import time
from typing import Any

import asyncio
import requests

from ..config import LLMSettings
from ..cost import CostEstimator
from ..errors import ProviderUnavailableError
from ..provider_base import LLMProvider
from ..types import ContentPart, LLMRequest, LLMResponse, ToolCall, Usage


class GeminiProvider(LLMProvider):
    name = "gemini"
    supports_tools = True
    supports_streaming = True
    supports_vision = True

    def __init__(self, settings: LLMSettings, cost_estimator: CostEstimator) -> None:
        self.settings = settings
        self.cost_estimator = cost_estimator

    def _resolve_model(self, logical_model: str) -> str:
        return self.settings.model_mapping[self.name].get(logical_model, logical_model)

    def _resolve_endpoint(self, provider_model: str) -> tuple[str, dict[str, str]]:
        if self.settings.google_api_key:
            return (
                f"https://generativelanguage.googleapis.com/v1beta/models/{provider_model}:generateContent?key={self.settings.google_api_key}",
                {"Content-Type": "application/json"},
            )
        if self.settings.vertex_project and self.settings.vertex_location:
            endpoint = (
                f"https://{self.settings.vertex_location}-aiplatform.googleapis.com/v1/projects/"
                f"{self.settings.vertex_project}/locations/{self.settings.vertex_location}/publishers/google/models/"
                f"{provider_model}:generateContent"
            )
            return (endpoint, {"Content-Type": "application/json"})
        raise ProviderUnavailableError("GOOGLE_API_KEY or Vertex config is required", provider=self.name)

    async def generate(self, req: LLMRequest) -> LLMResponse:
        started = time.perf_counter()
        provider_model = self._resolve_model(req.model)
        endpoint, headers = self._resolve_endpoint(provider_model)

        payload: dict[str, Any] = {
            "contents": [self._message_to_gemini(m.role, m.content) for m in req.messages],
            "generationConfig": {
                "temperature": req.temperature,
                "topP": req.top_p,
                "maxOutputTokens": req.max_output_tokens,
            },
        }
        if req.tools:
            payload["tools"] = [
                {
                    "functionDeclarations": [
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.json_schema,
                        }
                        for tool in req.tools
                    ]
                }
            ]

        try:
            resp = await asyncio.to_thread(requests.post, endpoint , json=payload, headers=headers, timeout=self.settings.request_timeout_ms / 1000)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:  # noqa: BLE001
            raise self.map_exception(exc) from exc

        latency_ms = int((time.perf_counter() - started) * 1000)
        candidates = data.get("candidates", [])
        first = candidates[0] if candidates else {}
        content_parts = first.get("content", {}).get("parts", [])
        text = "".join([p.get("text", "") for p in content_parts if p.get("text")])
        tool_calls = self._normalize_tool_calls(content_parts)

        usage_meta = data.get("usageMetadata", {})
        usage = self._usage_from_payload(usage_meta, latency_ms, provider_model)
        return LLMResponse(
            request_id=req.request_id,
            provider=self.name,
            provider_model=provider_model,
            output_text=text,
            tool_calls=tool_calls,
            usage=usage,
            finish_reason=first.get("finishReason", "stop"),
            raw=data if self.settings.llm_debug_raw_responses else None,
        )

    async def stream(self, req: LLMRequest):
        raise ProviderUnavailableError("Streaming is not implemented in this build", provider=self.name)

    def _message_to_gemini(self, role: str, content: str | list[ContentPart]) -> dict[str, Any]:
        parts: list[dict[str, Any]] = []
        if isinstance(content, str):
            parts.append({"text": content})
        else:
            for part in content:
                if part.type == "text" and part.text:
                    parts.append({"text": part.text})
                elif part.type == "image_url" and part.image_url:
                    parts.append({"fileData": {"fileUri": part.image_url}})
        mapped_role = "model" if role == "assistant" else "user"
        return {"role": mapped_role, "parts": parts}

    def _normalize_tool_calls(self, parts: list[dict[str, Any]]) -> list[ToolCall]:
        calls: list[ToolCall] = []
        for part in parts:
            fn = part.get("functionCall")
            if not fn:
                continue
            name = fn.get("name", "unknown")
            args = fn.get("args") if isinstance(fn.get("args"), dict) else {}
            call_id = self.stable_tool_call_id(name, args, fallback="gemini_tool")
            calls.append(ToolCall(id=call_id, name=name, arguments=args))
        return calls

    def _usage_from_payload(self, payload: dict[str, Any], latency_ms: int, provider_model: str) -> Usage:
        input_tokens = int(payload.get("promptTokenCount", 0))
        output_tokens = int(payload.get("candidatesTokenCount", 0))
        total_tokens = int(payload.get("totalTokenCount", input_tokens + output_tokens))
        return Usage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=self.cost_estimator.estimate_cost_usd(
                self.name, provider_model, input_tokens, output_tokens
            ),
            latency_ms=latency_ms,
        )
