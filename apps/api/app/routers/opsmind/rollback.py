from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from app.core.security import CurrentUser, require
from app.db.session import get_session
from app.db.models import RemediationAction
from app.services.audit import record_audit_event

router = APIRouter(prefix="/opsmind/rollback", tags=["rollback"])


@router.post("/{action_id}/execute")
def execute_rollback(
    action_id: str,
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(require("opsmind.rollback.execute")),
):
    action = session.exec(
        select(RemediationAction)
        .where(RemediationAction.org_id == current_user.org_id)
        .where(RemediationAction.id == action_id)
    ).first()
    if not action:
        return {"status": "not_found"}
    action.status = "rolled_back"
    session.add(action)
    session.commit()
    record_audit_event(
        session,
        "remedy.rolled_back",
        {"action_id": action_id},
        org_id=current_user.org_id,
        actor_user_id=current_user.id,
    )
    return {"status": "rolled_back"}
