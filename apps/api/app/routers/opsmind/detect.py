from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from app.core.security import CurrentUser, require
from app.db.session import get_session
from app.db.models import IncidentSignal

router = APIRouter(prefix="/opsmind/detect", tags=["detect"])


@router.get("/signals")
def list_signals(
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(require("opsmind.detect.read")),
):
    signals = session.exec(select(IncidentSignal).where(IncidentSignal.org_id == current_user.org_id)).all()
    return [
        {
            "id": str(signal.id),
            "incident_id": str(signal.incident_id),
            "type": signal.type,
            "payload": signal.payload,
        }
        for signal in signals
    ]
