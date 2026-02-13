from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from app.core.security import CurrentUser, require
from app.db.session import get_session
from app.db.models import RCAReport
from app.services.audit import record_audit_event

router = APIRouter(prefix="/opsmind/rca", tags=["rca"])


class RCAGenerateRequest(BaseModel):
    incident_id: str


@router.get("/reports")
def list_reports(
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(require("opsmind.rca.read")),
):
    reports = session.exec(select(RCAReport).where(RCAReport.org_id == current_user.org_id)).all()
    return [
        {
            "id": str(report.id),
            "incident_id": str(report.incident_id),
            "summary": report.summary,
            "evidence": report.evidence,
            "approved": report.approved,
        }
        for report in reports
    ]


@router.post("/generate")
def generate_report(
    payload: RCAGenerateRequest,
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(require("opsmind.rca.generate")),
):
    report = RCAReport(
        org_id=current_user.org_id,
        incident_id=payload.incident_id,
        summary="Generated RCA with citations.",
        evidence=[{"source": "incident", "detail": "Signal correlation"}],
        approved=False,
    )
    session.add(report)
    session.commit()
    record_audit_event(
        session,
        "rca.generated",
        {"report_id": str(report.id)},
        org_id=current_user.org_id,
        actor_user_id=current_user.id,
    )
    return {"id": str(report.id)}


@router.post("/{report_id}/approve")
def approve_report(
    report_id: str,
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(require("opsmind.rca.approve")),
):
    report = session.exec(
        select(RCAReport)
        .where(RCAReport.org_id == current_user.org_id)
        .where(RCAReport.id == report_id)
    ).first()
    if not report:
        return {"status": "not_found"}
    report.approved = True
    session.add(report)
    session.commit()
    record_audit_event(
        session,
        "rca.approved",
        {"report_id": report_id},
        org_id=current_user.org_id,
        actor_user_id=current_user.id,
    )
    return {"status": "approved"}
