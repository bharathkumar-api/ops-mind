from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ModelProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, messages: list[dict[str, str]], tools_schema: dict[str, Any] | None = None) -> dict[str, Any]: ...


class MockModelProvider(ModelProvider):
    def generate(self, prompt: str, messages: list[dict[str, str]], tools_schema: dict[str, Any] | None = None) -> dict[str, Any]:
        return {"text": "Deterministic mock response", "prompt": prompt, "messages": len(messages)}
