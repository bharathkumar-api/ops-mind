"""OpsMind API main application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.middleware import security_headers_middleware
from app.core.startup import init_application
import sys
from pathlib import Path

# Make local opsmind packages importable for orchestrator wiring
ROOT = Path(__file__).resolve().parents[3]
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

from app.routers import register_routers

settings = get_settings()

# Create FastAPI application
app = FastAPI(
    title="OpsMind API",
    description="Enterprise-safe AIOps platform API",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security headers middleware
app.middleware("http")(security_headers_middleware)

# Initialize application on startup
@app.on_event("startup")
def on_startup():
    """Initialize database and seed data on application startup."""
    init_application()

# Register all routers
register_routers(app)


# --- OpsMind orchestrator compatibility (chat endpoints) ---
from pathlib import Path
import os
import sys
import time
import logging
from fastapi import Header, HTTPException

ROOT = Path(__file__).resolve().parents[3]
# Ensure opsmind packages are importable when running this app in this repo layout
sys.path.extend(
    [
        str(ROOT / "opsmind" / "packages" / "contracts"),
        str(ROOT / "opsmind" / "packages" / "orchestrator"),
        str(ROOT / "opsmind" / "packages" / "tools"),
        str(ROOT / "opsmind" / "packages" / "storage"),
        str(ROOT / "opsmind" / "packages" / "common"),
    ]
)

try:
    from opsmind.contracts.v1.models import ChatSendRequest, ChatSendResponse, FeedbackRequest
    from opsmind.orchestrator.service import OrchestratorService
    from opsmind.storage.stores import InMemoryStore, RedisPostgresStore
    from opsmind.tools.registry import ToolRegistry
except Exception:  # pragma: no cover - non-fatal if opsmind packages not present
    ChatSendRequest = None
    ChatSendResponse = None
    FeedbackRequest = None
    OrchestratorService = None
    InMemoryStore = None
    RedisPostgresStore = None
    ToolRegistry = None

logger = logging.getLogger("opsmind.api")

# Only enable the endpoints if the opsmind packages are importable
if ChatSendRequest is not None:
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

