from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from opsmind.contracts.v1.models import TimeWindow, ToolArtifact, ToolCall, ToolResult


@dataclass
class ToolExecutionContext:
    conversation_id: str
    org_id: str
    project_id: str


class ToolRegistry:
    def __init__(self) -> None:
        self._tools = {
            "logs.query_error_breakdown": "Error spikes on /checkout endpoint.",
            "logs.query_timeouts_retries": "Retry volume increased by 40% in us-central.",
            "logs.compare_regions": "eu-west stable while us-central has elevated failures.",
            "traces.sample_failures": "Top failures include dependency payment-db timeout.",
            "traces.sample_slow": "P95 spans dominated by inventory service.",
            "traces.compare_regions": "Trace anomalies limited to one region.",
            "metrics.correlate_error_rate": "Error rate correlated with deploy at 10:15 UTC.",
            "metrics.latency_by_endpoint": "POST /checkout p99 latency increased 3x.",
            "metrics.compare_regions": "Regional divergence started 12 minutes ago.",
            "deploy.get_changes_near_window": "Deployment v2026.02.13 introduced retry config change.",
            "deploy.compare_region_rollouts": "Canary in us-central only.",
            "config.get_recent_changes": "Circuit breaker thresholds raised recently.",
        }

    def list_tools(self) -> list[str]:
        return sorted(self._tools.keys())

    def execute(self, tool_name: str, tool_input: dict[str, Any], ctx: ToolExecutionContext) -> tuple[ToolCall, ToolResult]:
        if tool_name not in self._tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        call = ToolCall(tool_name=tool_name, tool_input=tool_input)
        tw = tool_input.get("time_window")
        time_window = TimeWindow(**tw) if isinstance(tw, dict) else TimeWindow(start=datetime.utcnow()-timedelta(minutes=30), end=datetime.utcnow())
        artifact = ToolArtifact(
            uri=f"https://example.local/query/{uuid4()}",
            description=f"Mock artifact for {tool_name}",
        )
        result = ToolResult(
            tool_call_id=call.tool_call_id,
            tool_name=tool_name,
            source_system="mock",
            time_window=time_window,
            summary=self._tools[tool_name],
            artifacts=[artifact],
            raw_ref=f"mock://{tool_name}/{call.tool_call_id}",
        )
        return call, result
