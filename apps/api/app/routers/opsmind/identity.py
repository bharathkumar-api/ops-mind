from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from app.core.security import CurrentUser, require
from app.db.session import get_session
from app.db.models import Permission

router = APIRouter(prefix="/opsmind/identity", tags=["identity"])


@router.get("/me")
def read_me(current_user: CurrentUser = Depends(require("opsmind.identity.read"))):
    return {
        "id": str(current_user.id),
        "org_id": str(current_user.org_id),
        "email": current_user.email,
        "name": current_user.name,
    }


@router.get("/permissions")
def read_permissions(
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(require("opsmind.identity.permissions.read")),
):
    permissions = session.exec(select(Permission)).all()
    return [perm.key for perm in permissions]
