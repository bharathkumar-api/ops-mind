from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.core.security import CurrentUser, require
from app.db.session import get_session
from app.db.models import RemediationAction
from app.services.audit import record_audit_event

router = APIRouter(prefix="/opsmind/remedy", tags=["remedy"])


class RemedyProposeRequest(BaseModel):
    incident_id: str
    title: str
    details: dict = {}


@router.post("/propose")
def propose_remediation(
    payload: RemedyProposeRequest,
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(require("opsmind.remedy.propose")),
):
    action = RemediationAction(
        org_id=current_user.org_id,
        incident_id=payload.incident_id,
        title=payload.title,
        status="proposed",
        details=payload.details,
    )
    session.add(action)
    session.commit()
    record_audit_event(
        session,
        "remedy.proposed",
        {"action_id": str(action.id)},
        org_id=current_user.org_id,
        actor_user_id=current_user.id,
    )
    return {"id": str(action.id), "status": action.status}
