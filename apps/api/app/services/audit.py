from typing import Optional
from uuid import UUID
from sqlmodel import Session
from app.db.models import AuditEvent


def record_audit_event(
    session: Session,
    event_type: str,
    detail: dict,
    org_id: Optional[UUID] = None,
    actor_user_id: Optional[UUID] = None,
) -> None:
    event = AuditEvent(
        org_id=org_id,
        actor_user_id=actor_user_id,
        event_type=event_type,
        detail=detail,
    )
    session.add(event)
    session.commit()
