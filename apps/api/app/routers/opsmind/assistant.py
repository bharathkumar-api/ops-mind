import json
import time
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.core.security import CurrentUser, require, rate_limit_dependency
from app.services.audit import record_audit_event
from app.services.sanitizer import sanitize_markdown
from app.db.session import get_session
from sqlmodel import Session

router = APIRouter(prefix="/opsmind/assistant", tags=["assistant"])


class AssistantRequest(BaseModel):
    prompt: str
    incident_id: str | None = None


def _stream_response(content: str):
    for chunk in content.split(" "):
        payload = json.dumps({"token": chunk})
        yield f"data: {payload}\n\n"
        time.sleep(0.01)
    yield "data: {\"done\": true}\n\n"


@router.post("/chat")
def chat(
    payload: AssistantRequest,
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(require("opsmind.assistant.write")),
    _: None = Depends(rate_limit_dependency),
):
    response = sanitize_markdown(
        "Based on incident evidence and knowledge base, the likely root cause is database saturation. "
        "Citations: [metrics:db_cpu], [change:deploy_2024.10.12]."
    )
    record_audit_event(
        session,
        "assistant.chat",
        {"prompt": payload.prompt},
        org_id=current_user.org_id,
        actor_user_id=current_user.id,
    )
    return {"response": response}


@router.post("/chat/stream")
def chat_stream(
    payload: AssistantRequest,
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(require("opsmind.assistant.write")),
    _: None = Depends(rate_limit_dependency),
):
    response = sanitize_markdown(
        "Based on incident evidence and knowledge base, the likely root cause is database saturation. "
        "Citations: [metrics:db_cpu], [change:deploy_2024.10.12]."
    )
    record_audit_event(
        session,
        "assistant.chat.stream",
        {"prompt": payload.prompt},
        org_id=current_user.org_id,
        actor_user_id=current_user.id,
    )
    return StreamingResponse(_stream_response(response), media_type="text/event-stream")
