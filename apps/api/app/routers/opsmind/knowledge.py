from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from app.core.security import CurrentUser, require
from app.db.session import get_session
from app.db.models import KBDocument
from app.services.audit import record_audit_event

router = APIRouter(prefix="/opsmind/knowledge", tags=["knowledge"])


class KBDocumentCreate(BaseModel):
    title: str
    content: str


@router.get("/documents")
def list_documents(
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(require("opsmind.knowledge.read")),
):
    docs = session.exec(select(KBDocument).where(KBDocument.org_id == current_user.org_id)).all()
    return [{"id": str(doc.id), "title": doc.title, "content": doc.content} for doc in docs]


@router.post("/documents")
def create_document(
    payload: KBDocumentCreate,
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(require("opsmind.knowledge.write")),
):
    doc = KBDocument(org_id=current_user.org_id, title=payload.title, content=payload.content)
    session.add(doc)
    session.commit()
    record_audit_event(
        session,
        "knowledge.created",
        {"document_id": str(doc.id)},
        org_id=current_user.org_id,
        actor_user_id=current_user.id,
    )
    return {"id": str(doc.id)}
