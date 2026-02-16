from __future__ import annotations

from typing import Any, AsyncIterator, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ContentPart(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["text", "image_url"]
    text: str | None = None
    image_url: str | None = None

    @model_validator(mode="after")
    def validate_part(self) -> "ContentPart":
        if self.type == "text" and not self.text:
            raise ValueError("text is required when type=text")
        if self.type == "image_url" and not self.image_url:
            raise ValueError("image_url is required when type=image_url")
        return self


class Message(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["system", "user", "assistant", "tool"]
    content: str | list[ContentPart]
    name: str | None = None
    tool_call_id: str | None = None


class ToolSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str
    json_schema: dict[str, Any]
    version: str = "v1"


class ToolCall(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    arguments: dict[str, Any]


class Usage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    latency_ms: int = 0


ToolChoice = Literal["auto", "none"] | dict[str, Any]


class LLMRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    conversation_id: str | None = None
    messages: list[Message]
    model: str
    max_output_tokens: int | None = None
    temperature: float | None = None
    top_p: float | None = None
    tools: list[ToolSpec] | None = None
    tool_choice: ToolChoice | None = None
    stream: bool = False
    metadata: dict[str, Any] | None = None


class LLMResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    provider: str
    provider_model: str
    output_text: str
    tool_calls: list[ToolCall] = Field(default_factory=list)
    usage: Usage
    finish_reason: str
    raw: dict[str, Any] | None = None


class LLMResponseChunk(BaseModel):
    model_config = ConfigDict(extra="forbid")

    delta_text: str = ""
    delta_tool_calls: list[ToolCall] = Field(default_factory=list)
    is_final: bool = False
    usage_partial: Usage | None = None


LLMStream = AsyncIterator[LLMResponseChunk]
