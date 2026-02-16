from __future__ import annotations

from dataclasses import dataclass

from opsmind.contracts.v1.models import Scenario


@dataclass(frozen=True)
class ScenarioWorkflowSpec:
    scenario: Scenario
    required_slots: list[str]
    tool_plan: list[str]
    response_guidance: str


WORKFLOWS = {
    Scenario.HTTP_500_SPIKE: ScenarioWorkflowSpec(
        scenario=Scenario.HTTP_500_SPIKE,
        required_slots=["service", "environment", "time_window"],
        tool_plan=["logs.query_error_breakdown", "metrics.correlate_error_rate", "deploy.get_changes_near_window", "traces.sample_failures"],
        response_guidance="Prioritize error source and recent changes.",
    ),
    Scenario.LATENCY_OR_FAILURES: ScenarioWorkflowSpec(
        scenario=Scenario.LATENCY_OR_FAILURES,
        required_slots=["service", "environment"],
        tool_plan=["metrics.latency_by_endpoint", "traces.sample_slow", "logs.query_timeouts_retries"],
        response_guidance="Focus on latency distribution and retries.",
    ),
    Scenario.REGIONAL_PARTIAL_OUTAGE: ScenarioWorkflowSpec(
        scenario=Scenario.REGIONAL_PARTIAL_OUTAGE,
        required_slots=["service", "regions", "time_window"],
        tool_plan=["logs.compare_regions", "metrics.compare_regions", "traces.compare_regions", "deploy.compare_region_rollouts"],
        response_guidance="Contrast affected and healthy regions.",
    ),
    Scenario.GENERIC_RCA: ScenarioWorkflowSpec(
        scenario=Scenario.GENERIC_RCA,
        required_slots=["service"],
        tool_plan=["logs.query_error_breakdown", "metrics.correlate_error_rate", "config.get_recent_changes"],
        response_guidance="Gather broad evidence and narrow hypotheses.",
    ),
}
