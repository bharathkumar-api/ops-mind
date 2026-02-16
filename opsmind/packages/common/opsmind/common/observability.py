from __future__ import annotations

import json
import logging
import time
from contextlib import contextmanager


def configure_logging() -> None:
    class JsonFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            payload = {
                "level": record.levelname,
                "message": record.getMessage(),
                "logger": record.name,
                "timestamp": self.formatTime(record),
            }
            for key in ("request_id", "conversation_id", "scenario", "tool_calls_count", "latency_ms"):
                value = getattr(record, key, None)
                if value is not None:
                    payload[key] = value
            return json.dumps(payload)

    root = logging.getLogger()
    if root.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
    root.setLevel(logging.INFO)


@contextmanager
def trace_span(name: str):
    start = time.time()
    yield {"span": name}
    _ = (time.time() - start) * 1000
