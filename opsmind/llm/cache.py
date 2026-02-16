from __future__ import annotations

import hashlib
import time
from collections import OrderedDict

from .types import LLMRequest, LLMResponse


class LLMCache:
    def __init__(self, max_size: int = 256, ttl_seconds: int = 120) -> None:
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, tuple[float, LLMResponse]] = OrderedDict()

    def _key(self, provider: str, model: str, req: LLMRequest) -> str:
        prompt = "\n".join([
            f"{m.role}:{m.content if isinstance(m.content, str) else [p.model_dump() for p in m.content]}"
            for m in req.messages
        ])
        digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        return f"{provider}:{model}:{digest}"

    def is_cacheable(self, req: LLMRequest) -> bool:
        metadata = req.metadata or {}
        return bool(metadata.get("cacheable")) and not req.tools

    def get(self, provider: str, model: str, req: LLMRequest) -> LLMResponse | None:
        key = self._key(provider, model, req)
        value = self._cache.get(key)
        if not value:
            return None
        expires_at, response = value
        if time.time() > expires_at:
            self._cache.pop(key, None)
            return None
        self._cache.move_to_end(key)
        return response

    def set(self, provider: str, model: str, req: LLMRequest, res: LLMResponse) -> None:
        key = self._key(provider, model, req)
        self._cache[key] = (time.time() + self.ttl_seconds, res)
        self._cache.move_to_end(key)
        while len(self._cache) > self.max_size:
            self._cache.popitem(last=False)
