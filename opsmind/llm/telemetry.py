from __future__ import annotations

import json
import logging
from contextlib import contextmanager
from typing import Any, Iterator

logger = logging.getLogger("opsmind.llm")

try:  # pragma: no cover
    from opentelemetry import trace
except Exception:  # pragma: no cover
    trace = None


class Telemetry:
    def __init__(self, debug_raw: bool = False) -> None:
        self.debug_raw = debug_raw

    @contextmanager
    def span(self, name: str, attributes: dict[str, Any] | None = None) -> Iterator[None]:
        if trace is None:
            yield
            return
        tracer = trace.get_tracer("opsmind.llm")
        with tracer.start_as_current_span(name) as span:
            for key, value in (attributes or {}).items():
                span.set_attribute(key, value)
            yield

    def emit_event(self, **kwargs: Any) -> None:
        logger.info(json.dumps(kwargs, default=str))

    @staticmethod
    def safe_raw(raw: dict[str, Any] | None) -> dict[str, Any] | None:
        if raw is None:
            return None
        redacted = dict(raw)
        for key in ["api_key", "authorization", "x-api-key"]:
            if key in redacted:
                redacted[key] = "***"
        return redacted
