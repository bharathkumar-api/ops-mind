from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from app.core.security import CurrentUser, require
from app.db.session import get_session
from app.db.models import Incident
from app.services.audit import record_audit_event

router = APIRouter(prefix="/opsmind/incidents", tags=["incidents"])


class IncidentCreate(BaseModel):
    title: str
    severity: str
    description: str = ""


class IncidentUpdate(BaseModel):
    status: str


@router.get("/")
def list_incidents(
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(require("opsmind.incidents.read")),
):
    incidents = session.exec(select(Incident).where(Incident.org_id == current_user.org_id)).all()
    return [
        {
            "id": str(incident.id),
            "title": incident.title,
            "status": incident.status,
            "severity": incident.severity,
            "description": incident.description,
        }
        for incident in incidents
    ]


@router.post("/")
def create_incident(
    payload: IncidentCreate,
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(require("opsmind.incidents.write")),
):
    incident = Incident(
        org_id=current_user.org_id,
        title=payload.title,
        status="open",
        severity=payload.severity,
        description=payload.description,
    )
    session.add(incident)
    session.commit()
    record_audit_event(
        session,
        "incident.created",
        {"incident_id": str(incident.id), "title": payload.title},
        org_id=current_user.org_id,
        actor_user_id=current_user.id,
    )
    return {"id": str(incident.id)}


@router.patch("/{incident_id}")
def update_incident(
    incident_id: str,
    payload: IncidentUpdate,
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(require("opsmind.incidents.write")),
):
    incident = session.exec(
        select(Incident)
        .where(Incident.org_id == current_user.org_id)
        .where(Incident.id == incident_id)
    ).first()
    if not incident:
        return {"status": "not_found"}
    incident.status = payload.status
    session.add(incident)
    session.commit()
    record_audit_event(
        session,
        "incident.updated",
        {"incident_id": str(incident.id), "status": payload.status},
        org_id=current_user.org_id,
        actor_user_id=current_user.id,
    )
    return {"status": "updated"}
