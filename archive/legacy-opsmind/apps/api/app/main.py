from __future__ import annotations

import logging
import os
import sys
import time
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parents[3]
sys.path.extend(
    [
        str(ROOT / "packages" / "contracts"),
        str(ROOT / "packages" / "orchestrator"),
        str(ROOT / "packages" / "tools"),
        str(ROOT / "packages" / "storage"),
        str(ROOT / "packages" / "common"),
    ]
)

from opsmind.common.observability import configure_logging, trace_span
from opsmind.contracts.v1.models import ChatSendRequest, ChatSendResponse, FeedbackRequest
from opsmind.orchestrator.service import OrchestratorService
from opsmind.storage.stores import InMemoryStore, RedisPostgresStore
from opsmind.tools.registry import ToolRegistry

configure_logging()
logger = logging.getLogger("opsmind.api")

app = FastAPI(title="OpsMind API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


store_mode = os.getenv("OPSMIND_STORE", "memory")
if store_mode == "redis_postgres":
    state_store = RedisPostgresStore(
        redis_url=os.getenv("REDIS_URL", "redis://redis:6379/0"),
        postgres_dsn=os.getenv("POSTGRES_DSN", "postgresql://opsmind:opsmind@postgres:5432/opsmind"),
    )
else:
    state_store = InMemoryStore()

service = OrchestratorService(state_store, state_store, state_store, ToolRegistry())


@app.post("/v1/chat/send", response_model=ChatSendResponse)
def send_chat(
    request: ChatSendRequest,
    x_org_id: str | None = Header(default=None),
    x_project_id: str | None = Header(default=None),
):
    start = time.time()
    org_id = x_org_id or request.org_id or "local-org"
    project_id = x_project_id or request.project_id or "local-project"

    state = service.load_or_create(request.conversation_id, org_id, project_id)
    if request.context_overrides:
        service.apply_context_overrides(state, request.context_overrides)

    with trace_span("chat_turn"):
        response = service.handle_turn(state, request.message)

    latency = int((time.time() - start) * 1000)
    logger.info(
        "chat_turn_complete",
        extra={
            "conversation_id": state.conversation_id,
            "scenario": state.workflow.scenario.value,
            "tool_calls_count": len(state.execution.tool_calls),
            "latency_ms": latency,
        },
    )
    return ChatSendResponse(conversation_id=state.conversation_id, response=response)


@app.get("/v1/chat/conversations/{conversation_id}")
def get_conversation(conversation_id: str):
    state = state_store.get(conversation_id)
    if not state:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return state


@app.post("/v1/chat/feedback")
def post_feedback(feedback: FeedbackRequest):
    return {"status": "accepted", "conversation_id": feedback.conversation_id}


web_dir = ROOT / "apps" / "web"
if web_dir.exists():
    app.mount("/", StaticFiles(directory=web_dir, html=True), name="web")
