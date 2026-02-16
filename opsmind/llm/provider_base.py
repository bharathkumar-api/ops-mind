from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from typing import Any

from .errors import (
    AuthError,
    BadRequestError,
    OpsMindLLMError,
    ProviderUnavailableError,
    RateLimitError,
    TimeoutError,
)
from .types import LLMRequest, LLMResponse, LLMResponseChunk, Message, ToolCall, ToolSpec


class LLMProvider(ABC):
    name: str = "unknown"
    supports_tools: bool = True
    supports_streaming: bool = False
    supports_vision: bool = False

    @abstractmethod
    async def generate(self, req: LLMRequest) -> LLMResponse:
        raise NotImplementedError

    async def stream(self, req: LLMRequest):
        raise NotImplementedError("Streaming is not supported by this provider")

    def map_exception(self, exc: Exception) -> OpsMindLLMError:
        text = str(exc).lower()
        if isinstance(exc, OpsMindLLMError):
            return exc
        if "auth" in text or "unauthorized" in text or "api key" in text:
            return AuthError(str(exc), provider=self.name)
        if "rate" in text or "429" in text or "quota" in text:
            return RateLimitError(str(exc), provider=self.name)
        if "timeout" in text:
            return TimeoutError(str(exc), provider=self.name)
        if "invalid" in text or "400" in text or "schema" in text:
            return BadRequestError(str(exc), provider=self.name)
        return ProviderUnavailableError(str(exc), provider=self.name)

    @staticmethod
    def message_to_text(msg: Message) -> str:
        if isinstance(msg.content, str):
            return msg.content
        parts: list[str] = []
        for part in msg.content:
            if part.type == "text" and part.text:
                parts.append(part.text)
            elif part.type == "image_url" and part.image_url:
                parts.append(f"[image:{part.image_url}]")
        return "\n".join(parts)

    @staticmethod
    def tool_spec_to_openai(tool: ToolSpec) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.json_schema,
                "strict": False,
            },
        }

    @staticmethod
    def safe_parse_json(value: str | dict[str, Any] | None) -> dict[str, Any]:
        if value is None:
            return {}
        if isinstance(value, dict):
            return value
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {"value": parsed}
        except json.JSONDecodeError:
            return {"raw": value}

    @staticmethod
    def stable_tool_call_id(name: str, arguments: dict[str, Any], fallback: str = "tool") -> str:
        blob = json.dumps({"n": name, "a": arguments}, sort_keys=True).encode("utf-8")
        digest = hashlib.sha1(blob).hexdigest()[:12]
        return f"{fallback}_{digest}"


__all__ = ["LLMProvider", "ToolCall", "LLMResponseChunk"]
