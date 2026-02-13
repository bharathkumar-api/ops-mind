from opsmind.contracts.v1.models import ChannelContext, ConversationState, TenantContext
from opsmind.orchestrator.service import OrchestratorService
from opsmind.storage.stores import InMemoryStore
from opsmind.tools.registry import ToolRegistry


def make_service():
    store = InMemoryStore()
    return OrchestratorService(store, store, store, ToolRegistry()), store


def test_scenario_classification():
    service, _ = make_service()
    from opsmind.contracts.v1.models import Scenario
    assert service.classify_scenario("Seeing HTTP 500 spike") == Scenario.HTTP_500_SPIKE
    assert service.classify_scenario("regional outage in us-east") == Scenario.REGIONAL_PARTIAL_OUTAGE
    assert service.classify_scenario("latency and timeout rising") == Scenario.LATENCY_OR_FAILURES


def test_needs_info_when_slots_missing():
    service, store = make_service()
    state = ConversationState(
        tenant=TenantContext(org_id="o1", project_id="p1"),
        channel=ChannelContext(routing_key="web:o1:new"),
    )
    store.create(state)
    response = service.handle_turn(state, "500 errors everywhere")
    assert response.status == "needs_info"
    assert response.followup_questions


def test_evidence_first_hypothesis_enforced():
    service, store = make_service()
    state = ConversationState(
        tenant=TenantContext(org_id="o1", project_id="p1"),
        channel=ChannelContext(routing_key="web:o1:new"),
    )
    state.slots.service = "checkout"
    state.slots.environment = "prod"
    from opsmind.contracts.v1.models import TimeWindow
    state.slots.time_window = TimeWindow(start="2026-02-13T10:00:00", end="2026-02-13T10:30:00")
    store.create(state)
    response = service.handle_turn(state, "500 spike in checkout")
    assert response.status == "complete"
    assert all(h.evidence_refs for h in response.hypotheses)


def test_schema_validation_extra_forbid():
    from pydantic import ValidationError
    from opsmind.contracts.v1.models import ConversationState

    try:
        ConversationState.model_validate({"tenant": {"org_id": "o", "project_id": "p", "bad": 1}, "channel": {"routing_key": "x"}})
        assert False
    except ValidationError:
        assert True


def test_tool_execution_ledger_appended():
    service, store = make_service()
    state = ConversationState(
        tenant=TenantContext(org_id="o1", project_id="p1"),
        channel=ChannelContext(routing_key="web:o1:new"),
    )
    state.slots.service = "checkout"
    state.slots.environment = "prod"
    store.create(state)
    service.handle_turn(state, "latency spike")
    assert len(state.execution.tool_calls) > 0
    assert len(state.execution.tool_results) == len(state.execution.tool_calls)
