from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from app.core.security import CurrentUser, require
from app.db.session import get_session
from app.db.models import RemediationAction
from app.services.audit import record_audit_event

router = APIRouter(prefix="/opsmind/approvals", tags=["approvals"])


@router.post("/{action_id}/approve")
def approve_remediation(
    action_id: str,
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(require("opsmind.approvals.approve")),
):
    action = session.exec(
        select(RemediationAction)
        .where(RemediationAction.org_id == current_user.org_id)
        .where(RemediationAction.id == action_id)
    ).first()
    if not action:
        return {"status": "not_found"}
    action.status = "approved"
    session.add(action)
    session.commit()
    record_audit_event(
        session,
        "remedy.approved",
        {"action_id": action_id},
        org_id=current_user.org_id,
        actor_user_id=current_user.id,
    )
    return {"status": "approved"}
