from __future__ import annotations

from datetime import datetime

from opsmind.contracts.v1.models import (
    ChannelContext,
    ConversationState,
    Message,
    MessageRole,
    Scenario,
    TenantContext,
)
from opsmind.orchestrator.presenter import present_complete, present_needs_info
from opsmind.orchestrator.workflows import WORKFLOWS
from opsmind.storage.stores import ConversationStateStore, TranscriptStore, ToolResultStore
from opsmind.tools.registry import ToolExecutionContext, ToolRegistry


class OrchestratorService:
    def __init__(
        self,
        state_store: ConversationStateStore,
        transcript_store: TranscriptStore,
        tool_result_store: ToolResultStore,
        tool_registry: ToolRegistry,
        max_tool_calls_per_turn: int = 4,
    ) -> None:
        self.state_store = state_store
        self.transcript_store = transcript_store
        self.tool_result_store = tool_result_store
        self.tool_registry = tool_registry
        self.max_tool_calls_per_turn = max_tool_calls_per_turn

    def classify_scenario(self, text: str) -> Scenario:
        lower = text.lower()
        if "500" in lower:
            return Scenario.HTTP_500_SPIKE
        if "region" in lower or "regional" in lower:
            return Scenario.REGIONAL_PARTIAL_OUTAGE
        if "latency" in lower or "timeout" in lower or "failure" in lower:
            return Scenario.LATENCY_OR_FAILURES
        return Scenario.GENERIC_RCA

    def _required_missing(self, state: ConversationState) -> list[str]:
        spec = WORKFLOWS[state.workflow.scenario]
        missing: list[str] = []
        for slot in spec.required_slots:
            value = getattr(state.slots, slot)
            if value is None or value == []:
                missing.append(slot)
        return missing

    def _question_for_slot(self, slot: str) -> str:
        return {
            "service": "Which service is impacted?",
            "environment": "Which environment is impacted (prod/staging)?",
            "regions": "Which regions are affected?",
            "time_window": "What time window should we investigate?",
        }.get(slot, f"Please provide {slot}.")

    def load_or_create(self, conversation_id: str | None, org_id: str, project_id: str) -> ConversationState:
        if conversation_id:
            existing = self.state_store.get(conversation_id)
            if existing:
                return existing
        routing_key = f"web:{org_id}:{conversation_id or 'new'}"
        state = ConversationState(
            tenant=TenantContext(org_id=org_id, project_id=project_id),
            channel=ChannelContext(routing_key=routing_key),
        )
        return self.state_store.create(state)

    def apply_context_overrides(self, state: ConversationState, overrides: dict) -> None:
        for key in ["service", "environment", "regions", "symptoms", "actions_taken", "hypotheses", "open_questions"]:
            if key in overrides and overrides[key] is not None:
                setattr(state.slots, key, overrides[key])
        if "time_window" in overrides and isinstance(overrides["time_window"], dict):
            tw = overrides["time_window"]
            from opsmind.contracts.v1.models import TimeWindow
            state.slots.time_window = TimeWindow(**tw)

    def handle_turn(self, state: ConversationState, user_message: str):
        safe_message = user_message.strip()[:2000]
        state.messages.append(Message(role=MessageRole.user, text=safe_message))
        self.transcript_store.append_message(state.conversation_id, state.messages[-1])

        state.workflow.scenario = self.classify_scenario(safe_message)
        missing = self._required_missing(state)
        state.workflow.missing_slots = missing

        if missing:
            response = present_needs_info([self._question_for_slot(s) for s in missing])
            state.messages.append(Message(role=MessageRole.assistant, text=response.primary_text))
            self.transcript_store.append_message(state.conversation_id, state.messages[-1])
            self.state_store.save(state)
            return response

        spec = WORKFLOWS[state.workflow.scenario]
        ctx = ToolExecutionContext(
            conversation_id=state.conversation_id,
            org_id=state.tenant.org_id,
            project_id=state.tenant.project_id,
        )
        for tool_name in spec.tool_plan[: self.max_tool_calls_per_turn]:
            tool_input = {"service": state.slots.service, "environment": state.slots.environment}
            if state.slots.time_window:
                tool_input["time_window"] = state.slots.time_window.model_dump(mode="json")
            call, result = self.tool_registry.execute(tool_name, tool_input, ctx)
            state.execution.tool_calls.append(call)
            state.execution.tool_results.append(result)
            self.tool_result_store.store_tool_result(state.conversation_id, result)

        response = present_complete(state.execution.tool_results[-self.max_tool_calls_per_turn :])
        state.summary.text = response.primary_text
        state.summary.updated_at = datetime.utcnow()
        state.messages.append(Message(role=MessageRole.assistant, text=response.primary_text))
        self.transcript_store.append_message(state.conversation_id, state.messages[-1])
        self.state_store.save(state)
        return response
