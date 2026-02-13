from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from app.core.security import CurrentUser, require
from app.db.session import get_session
from app.db.models import AuditEvent

router = APIRouter(prefix="/opsmind/governance", tags=["governance"])


@router.get("/audit")
def list_audit_events(
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(require("opsmind.governance.audit.read")),
):
    events = session.exec(select(AuditEvent).where(AuditEvent.org_id == current_user.org_id)).all()
    return [
        {
            "id": str(event.id),
            "event_type": event.event_type,
            "detail": event.detail,
            "created_at": event.created_at.isoformat(),
        }
        for event in events
    ]


@router.post("/export")
def export_audit(
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(require("opsmind.governance.export")),
):
    events = session.exec(select(AuditEvent).where(AuditEvent.org_id == current_user.org_id)).all()
    return {"count": len(events)}
