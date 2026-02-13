from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from app.core.security import CurrentUser, require
from app.db.session import get_session
from app.db.models import User, Role, UserRole
from app.services.audit import record_audit_event

router = APIRouter(prefix="/opsmind/admin", tags=["admin"])


class RoleAssignRequest(BaseModel):
    user_id: str
    role_id: str


@router.get("/users")
def list_users(
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(require("opsmind.admin.users.manage")),
):
    users = session.exec(select(User).where(User.org_id == current_user.org_id)).all()
    return [{"id": str(user.id), "email": user.email, "name": user.name} for user in users]


@router.get("/roles")
def list_roles(
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(require("opsmind.admin.roles.manage")),
):
    roles = session.exec(select(Role).where(Role.org_id == current_user.org_id)).all()
    return [{"id": str(role.id), "name": role.name} for role in roles]


@router.post("/roles/assign")
def assign_role(
    payload: RoleAssignRequest,
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(require("opsmind.admin.roles.manage")),
):
    user_role = UserRole(org_id=current_user.org_id, user_id=payload.user_id, role_id=payload.role_id)
    session.add(user_role)
    session.commit()
    record_audit_event(
        session,
        "admin.role.assign",
        {"user_id": payload.user_id, "role_id": payload.role_id},
        org_id=current_user.org_id,
        actor_user_id=current_user.id,
    )
    return {"status": "assigned"}
