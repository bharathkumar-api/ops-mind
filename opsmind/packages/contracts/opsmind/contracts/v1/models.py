from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class MessageRole(str, Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


class ResponseStatus(str, Enum):
    complete = "complete"
    needs_info = "needs_info"
    running_async = "running_async"


class Scenario(str, Enum):
    HTTP_500_SPIKE = "HTTP_500_SPIKE"
    LATENCY_OR_FAILURES = "LATENCY_OR_FAILURES"
    REGIONAL_PARTIAL_OUTAGE = "REGIONAL_PARTIAL_OUTAGE"
    GENERIC_RCA = "GENERIC_RCA"


class TimeWindow(StrictBaseModel):
    start: datetime | None = None
    end: datetime | None = None


class TenantContext(StrictBaseModel):
    org_id: str
    project_id: str


class ChannelContext(StrictBaseModel):
    channel: Literal["web"] = "web"
    routing_key: str


class Message(StrictBaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid4()))
    role: MessageRole
    text: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Summary(StrictBaseModel):
    text: str = ""
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class RCASlots(StrictBaseModel):
    service: str | None = None
    environment: str | None = None
    regions: list[str] = Field(default_factory=list)
    time_window: TimeWindow | None = None
    symptoms: list[str] = Field(default_factory=list)
    hypotheses: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    actions_taken: list[str] = Field(default_factory=list)


class ToolArtifact(StrictBaseModel):
    artifact_id: str = Field(default_factory=lambda: str(uuid4()))
    uri: str
    kind: str = "link"
    description: str | None = None


class ToolCall(StrictBaseModel):
    tool_call_id: str = Field(default_factory=lambda: str(uuid4()))
    tool_name: str
    tool_input: dict[str, Any]
    invoked_at: datetime = Field(default_factory=datetime.utcnow)


class ToolResult(StrictBaseModel):
    tool_call_id: str
    tool_name: str
    source_system: str
    time_window: TimeWindow | None = None
    summary: str
    artifacts: list[ToolArtifact] = Field(default_factory=list)
    raw_ref: str | None = None


class EvidenceRef(StrictBaseModel):
    ref_type: Literal["tool_call", "artifact"]
    ref_id: str
    description: str


class Hypothesis(StrictBaseModel):
    statement: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_refs: list[EvidenceRef]


class WorkflowState(StrictBaseModel):
    scenario: Scenario = Scenario.GENERIC_RCA
    step: str = "start"
    missing_slots: list[str] = Field(default_factory=list)
    engine_state: dict[str, Any] = Field(default_factory=dict)


class ExecutionLedger(StrictBaseModel):
    tool_calls: list[ToolCall] = Field(default_factory=list)
    tool_results: list[ToolResult] = Field(default_factory=list)


class ConversationState(StrictBaseModel):
    conversation_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant: TenantContext
    channel: ChannelContext
    messages: list[Message] = Field(default_factory=list)
    summary: Summary = Field(default_factory=Summary)
    slots: RCASlots = Field(default_factory=RCASlots)
    workflow: WorkflowState = Field(default_factory=WorkflowState)
    execution: ExecutionLedger = Field(default_factory=ExecutionLedger)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ResponseModel(StrictBaseModel):
    status: ResponseStatus
    primary_text: str
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    evidence: list[EvidenceRef] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    followup_questions: list[str] = Field(default_factory=list)
    notes: str | None = None
    async_job_id: str | None = None


class ChatSendRequest(StrictBaseModel):
    message: str
    conversation_id: str | None = None
    org_id: str | None = None
    project_id: str | None = None
    context_overrides: dict[str, Any] = Field(default_factory=dict)


class ChatSendResponse(StrictBaseModel):
    conversation_id: str
    response: ResponseModel


class FeedbackRequest(StrictBaseModel):
    conversation_id: str
    rating: int = Field(ge=1, le=5)
    comment: str | None = None
