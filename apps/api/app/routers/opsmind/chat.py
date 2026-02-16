from __future__ import annotations

from typing import Any, Dict
from uuid import uuid4
from datetime import datetime
from pathlib import Path
import sys
import os
import logging

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/v1/chat", tags=["chat"])


class ChatSendRequest(BaseModel):
    message: str
    conversation_id: str | None = None
    org_id: str | None = None
    project_id: str | None = None
    context_overrides: dict[str, Any] = Field(default_factory=dict)


class ResponseModel(BaseModel):
    status: str
    primary_text: str


class ChatSendResponse(BaseModel):
    conversation_id: str
    response: ResponseModel


class FeedbackRequest(BaseModel):
    conversation_id: str
    rating: int
    comment: str | None = None


# Simple in-memory store for conversations
_STORE: Dict[str, Dict] = {}


# Try to wire to the full opsmind orchestrator if available
ROOT = Path(__file__).resolve().parents[5]
# Ensure the repo root is first so the top-level `opsmind` package can be imported
sys.path.insert(0, str(ROOT))

sys.path.extend(
    [
        str(ROOT / "opsmind" / "packages" / "contracts"),
        str(ROOT / "opsmind" / "packages" / "orchestrator"),
        str(ROOT / "opsmind" / "packages" / "tools"),
        str(ROOT / "opsmind" / "packages" / "storage"),
        str(ROOT / "opsmind" / "packages" / "common"),
    ]
)

logger = logging.getLogger("opsmind.chat")

USE_ORCHESTRATOR = False
service = None
ops_models = None
try:
    import importlib

    importlib.invalidate_caches()
    # If opsmind already loaded, extend its __path__ to include package folders
    if "opsmind" in sys.modules:
        opsmod = sys.modules["opsmind"]
        extra_paths = [
            str(ROOT / "opsmind" / "packages" / "contracts"),
            str(ROOT / "opsmind" / "packages" / "orchestrator"),
            str(ROOT / "opsmind" / "packages" / "tools"),
            str(ROOT / "opsmind" / "packages" / "storage"),
            str(ROOT / "opsmind" / "packages" / "common"),
        ]
        if hasattr(opsmod, "__path__"):
            for p in extra_paths:
                if p not in opsmod.__path__:
                    opsmod.__path__.append(p)

    # Provide a lightweight stub for psycopg if it's not installed so imports succeed
    if 'psycopg' not in sys.modules:
        import types

        mod = types.ModuleType('psycopg')

        def _psy_connect(*a, **kw):
            raise RuntimeError('psycopg not installed')

        mod.connect = _psy_connect
        sys.modules['psycopg'] = mod
    # Provide a lightweight stub for redis if it's not installed
    if 'redis' not in sys.modules:
        import types

        redis_mod = types.ModuleType('redis')

        class _DummyRedis:
            @classmethod
            def from_url(cls, *a, **kw):
                return cls()

            def get(self, *a, **kw):
                return None

            def set(self, *a, **kw):
                return None

        redis_mod.Redis = _DummyRedis
        sys.modules['redis'] = redis_mod

    from opsmind.contracts.v1.models import ChatSendResponse as OpsChatSendResponse  # type: ignore
    from opsmind.orchestrator.service import OrchestratorService  # type: ignore
    from opsmind.storage.stores import InMemoryStore  # type: ignore
    from opsmind.tools.registry import ToolRegistry  # type: ignore

    # Prefer DATABASE_URL for Postgres-only deployments (no Redis required)
    database_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_DSN")
    if database_url:
        # Use PostgresStore when DATABASE_URL is provided. Allow exceptions to surface
        # so the operator can see DB connectivity issues instead of silently falling back.
        from opsmind.storage.stores import PostgresStore  # type: ignore

        state_store = PostgresStore(database_url)
    else:
        # Legacy flag: if explicitly set to redis_postgres, attempt that (requires redis + psycopg)
        store_mode = os.getenv("OPSMIND_STORE", "memory")
        if store_mode == "redis_postgres":
            try:
                from opsmind.storage.stores import RedisPostgresStore  # type: ignore

                state_store = RedisPostgresStore(
                    redis_url=os.getenv("REDIS_URL", "redis://redis:6379/0"),
                    postgres_dsn=os.getenv("POSTGRES_DSN", "postgresql://opsmind:opsmind@postgres:5432/opsmind"),
                )
            except Exception:
                state_store = InMemoryStore()
        else:
            state_store = InMemoryStore()

    service = OrchestratorService(state_store, state_store, state_store, ToolRegistry())
    USE_ORCHESTRATOR = True
    ops_models = {
        "ChatSendResponse": OpsChatSendResponse,
    }
    logger.info("Wired chat router to opsmind orchestrator")
except Exception as e:  # pragma: no cover - optional runtime wiring
    ORCH_ERROR = str(e)
    logger.debug("Orchestrator not available: %s", e)


@router.post("/send", response_model=ChatSendResponse)
def send_chat(request: ChatSendRequest, x_org_id: str | None = Header(default=None), x_project_id: str | None = Header(default=None)):
    # If orchestrator available, delegate
    if USE_ORCHESTRATOR and service is not None:
        org_id = x_org_id or request.org_id or "local-org"
        project_id = x_project_id or request.project_id or "local-project"
        state = service.load_or_create(request.conversation_id, org_id, project_id)
        if request.context_overrides:
            service.apply_context_overrides(state, request.context_overrides)

        response = service.handle_turn(state, request.message)
        return {"conversation_id": state.conversation_id, "response": response}

    # Fallback minimal behavior
    conv_id = request.conversation_id or str(uuid4())
    now = datetime.utcnow().isoformat()
    convo = _STORE.get(conv_id)
    if not convo:
        convo = {"conversation_id": conv_id, "messages": [], "created_at": now, "updated_at": now}
        _STORE[conv_id] = convo

    msg = {"role": "user", "text": request.message, "created_at": now}
    convo["messages"].append(msg)
    convo["updated_at"] = now

    # Minimal response: echo back a concise assistant reply
    reply_text = f"Received your message: {request.message[:200]}"
    assistant_msg = {"role": "assistant", "text": reply_text, "created_at": now}
    convo["messages"].append(assistant_msg)

    response = ResponseModel(status="complete", primary_text=reply_text)
    return ChatSendResponse(conversation_id=conv_id, response=response)


@router.get("/conversations/{conversation_id}")
def get_conversation(conversation_id: str):
    convo = _STORE.get(conversation_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return convo


@router.post("/feedback")
def post_feedback(feedback: FeedbackRequest):
    # Accept feedback but do not store persistently in this minimal implementation
    return {"status": "accepted", "conversation_id": feedback.conversation_id}
