from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from pydantic import Field

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except Exception:  # pragma: no cover
    from pydantic import BaseModel as BaseSettings

    class SettingsConfigDict(dict):
        pass


DEFAULT_MODEL_MAPPING: dict[str, dict[str, str]] = {
    "openai": {
        "fast": "gpt-4o-mini",
        "balanced": "gpt-4.1-mini",
        "reasoning": "o3-mini",
    },
    "anthropic": {
        "fast": "claude-3-5-haiku-latest",
        "balanced": "claude-3-5-sonnet-latest",
        "reasoning": "claude-3-7-sonnet-latest",
    },
    "gemini": {
        "fast": "gemini-2.0-flash",
        "balanced": "gemini-1.5-pro",
        "reasoning": "gemini-1.5-pro",
    },
}


class LLMSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    llm_providers_enabled: list[str] = Field(default_factory=lambda: ["openai", "anthropic", "gemini"])
    llm_default_provider: str = "gemini"

    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    google_api_key: str | None = None

    vertex_project: str | None = None
    vertex_location: str | None = None

    request_timeout_ms: int = 30_000
    max_retries: int = 2
    max_cost_usd_per_request: float = 1.0
    max_tokens_per_request: int = 32_000

    llm_model_mapping_json: str | None = None
    llm_pricing_json: str | None = None
    llm_debug_raw_responses: bool = False

    @property
    def model_mapping(self) -> dict[str, dict[str, str]]:
        if not self.llm_model_mapping_json:
            return DEFAULT_MODEL_MAPPING
        parsed: dict[str, dict[str, str]] = json.loads(self.llm_model_mapping_json)
        return parsed

    @property
    def pricing_override(self) -> dict[str, Any]:
        if not self.llm_pricing_json:
            return {}
        return json.loads(self.llm_pricing_json)


@lru_cache(maxsize=1)
def get_settings() -> LLMSettings:
    return LLMSettings()  # type: ignore[call-arg]
