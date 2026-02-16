from __future__ import annotations

import re
from dataclasses import dataclass, field

from .errors import BadRequestError
from .types import LLMRequest, ToolSpec

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"\+?\d[\d\-\s]{7,}\d")


@dataclass
class PolicyConfig:
    scenario_tool_allowlist: dict[str, set[str]] = field(default_factory=dict)
    denied_tool_names: set[str] = field(default_factory=lambda: {"shell_exec", "delete_all"})
    max_tool_schema_bytes: int = 64_000
    pii_redaction_enabled: bool = True


class PolicyEngine:
    def __init__(self, config: PolicyConfig | None = None) -> None:
        self.config = config or PolicyConfig()

    def enforce(self, req: LLMRequest) -> LLMRequest:
        tools = req.tools or []
        scenario = (req.metadata or {}).get("scenario")
        allowlist = self.config.scenario_tool_allowlist.get(scenario, set()) if scenario else set()
        validated: list[ToolSpec] = []
        for tool in tools:
            if tool.name in self.config.denied_tool_names:
                raise BadRequestError(f"Denied tool name: {tool.name}")
            if allowlist and tool.name not in allowlist:
                raise BadRequestError(f"Tool '{tool.name}' not allowlisted for scenario '{scenario}'")
            if len(str(tool.json_schema).encode("utf-8")) > self.config.max_tool_schema_bytes:
                raise BadRequestError(f"Tool schema for '{tool.name}' exceeds maximum size")
            validated.append(tool)
        req.tools = validated
        return req

    def redact_pii(self, text: str) -> str:
        if not self.config.pii_redaction_enabled:
            return text
        text = EMAIL_RE.sub("[REDACTED_EMAIL]", text)
        return PHONE_RE.sub("[REDACTED_PHONE]", text)
