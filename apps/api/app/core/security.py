from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from uuid import UUID
import time
import io
import requests
from jose import jwt
from jose.exceptions import JWTError
from fastapi import Depends, Header, HTTPException, Request, status
from sqlmodel import Session, select
import casbin
from casbin import persist
from app.core.config import get_settings
from app.db.session import get_session
from app.db.models import (
    Org,
    User,
    OrgMembership,
    Role,
    Permission,
    RolePermission,
    UserRole,
)
from app.services.audit import record_audit_event


@dataclass
class CurrentUser:
    id: UUID
    org_id: UUID
    email: str
    name: str
    sub: str


class MemoryAdapter(persist.Adapter):
    def __init__(self, policies: list[list[str]]):
        self.policies = policies

    def load_policy(self, model):
        for policy in self.policies:
            persist.load_policy_line(", ".join(policy), model)

    def save_policy(self, model):
        return False

    def add_policy(self, sec, ptype, rule):
        return False

    def remove_policy(self, sec, ptype, rule):
        return False

    def remove_filtered_policy(self, sec, ptype, field_index, *field_values):
        return False


_model_text = """
[request_definition]
r = sub, dom, obj

[policy_definition]
p = sub, dom, obj

[role_definition]
g = _, _, _

[policy_effect]
e = some(where (p.eft == allow))

[matchers]
m = g(r.sub, p.sub, r.dom) && r.dom == p.dom && r.obj == p.obj
"""


rate_state: dict[str, tuple[int, float]] = {}


def _rate_limited(request: Request) -> None:
    settings = get_settings()
    key = f"{request.client.host}:{request.url.path}"
    count, start = rate_state.get(key, (0, time.time()))
    now = time.time()
    if now - start > 60:
        count, start = 0, now
    count += 1
    rate_state[key] = (count, start)
    if count > settings.rate_limit_per_minute:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")


async def rate_limit_dependency(request: Request) -> None:
    _rate_limited(request)


def _build_enforcer(session: Session, org_id: UUID) -> casbin.Enforcer:
    policies: list[list[str]] = []
    roles = {role.id: role for role in session.exec(select(Role).where(Role.org_id == org_id)).all()}
    permissions = {perm.id: perm for perm in session.exec(select(Permission)).all()}
    for role_permission in session.exec(select(RolePermission).where(RolePermission.org_id == org_id)).all():
        role = roles.get(role_permission.role_id)
        permission = permissions.get(role_permission.permission_id)
        if role and permission:
            policies.append(["p", role.name, str(org_id), permission.key])
    for user_role in session.exec(select(UserRole).where(UserRole.org_id == org_id)).all():
        role = roles.get(user_role.role_id)
        if role:
            policies.append(["g", str(user_role.user_id), role.name, str(org_id)])
    adapter = MemoryAdapter(policies)
    # Build a Casbin model from the model text and create the enforcer
    model = casbin.model.Model()
    model.load_model_from_text(_model_text)
    enforcer = casbin.Enforcer(model, adapter)
    enforcer.load_policy()
    return enforcer


def _create_org_for_user(session: Session, user: User) -> UUID:
    org = Org(name=f"{user.email.split('@')[-1]} org")
    session.add(org)
    session.commit()
    session.refresh(org)
    from app.seed import seed_roles, seed_sample_data
    seed_roles(session, org.id)
    seed_sample_data(session, org.id)
    membership = OrgMembership(org_id=org.id, user_id=user.id)
    session.add(membership)
    owner_role = session.exec(select(Role).where(Role.name == "owner").where(Role.org_id == org.id)).first()
    if owner_role:
        session.add(UserRole(org_id=org.id, user_id=user.id, role_id=owner_role.id))
    session.commit()
    return org.id


def _bootstrap_user(session: Session, sub: str, email: str, name: str) -> CurrentUser:
    user = session.exec(select(User).where(User.sub == sub)).first()
    if user:
        org_id = user.org_id or _create_org_for_user(session, user)
        return CurrentUser(id=user.id, org_id=org_id, email=user.email, name=user.name, sub=user.sub)
    user = User(sub=sub, email=email, name=name)
    session.add(user)
    session.commit()
    session.refresh(user)
    org_id = _create_org_for_user(session, user)
    user.org_id = org_id
    session.add(user)
    session.commit()
    return CurrentUser(id=user.id, org_id=org_id, email=user.email, name=user.name, sub=user.sub)


def _decode_jwt(token: str) -> dict:
    settings = get_settings()
    if settings.dev_auth_bypass:
        return {"sub": "dev-user", "email": "dev@opsmind.local", "name": "Dev User"}
    if not settings.jwks_url:
        raise HTTPException(status_code=401, detail="JWKS_URL not configured")
    jwks = requests.get(settings.jwks_url, timeout=5).json()
    headers = jwt.get_unverified_header(token)
    key = next((k for k in jwks.get("keys", []) if k.get("kid") == headers.get("kid")), None)
    if not key:
        raise HTTPException(status_code=401, detail="Invalid token")
    return jwt.decode(
        token,
        key,
        algorithms=[key.get("alg", "RS256")],
        audience=settings.jwt_audience or None,
        issuer=settings.jwt_issuer or None,
    )


def get_current_user(
    authorization: Optional[str] = Header(default=None),
    session: Session = Depends(get_session),
) -> CurrentUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        record_audit_event(session, "auth.failure", {"reason": "missing_token"})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    token = authorization.split(" ", 1)[1]
    try:
        payload = _decode_jwt(token)
    except (JWTError, HTTPException) as exc:
        record_audit_event(session, "auth.failure", {"reason": "invalid_token"})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
    sub = payload.get("sub")
    if not sub:
        record_audit_event(session, "auth.failure", {"reason": "missing_sub"})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    email = payload.get("email", "")
    name = payload.get("name", "")
    return _bootstrap_user(session, sub, email, name)


def require(permission: str):
    def dependency(
        current_user: CurrentUser = Depends(get_current_user),
        session: Session = Depends(get_session),
    ) -> CurrentUser:
        enforcer = _build_enforcer(session, current_user.org_id)
        if not enforcer.enforce(str(current_user.id), str(current_user.org_id), permission):
            record_audit_event(
                session,
                "rbac.denied",
                {"permission": permission},
                org_id=current_user.org_id,
                actor_user_id=current_user.id,
            )
            raise HTTPException(status_code=403, detail="Forbidden")
        return current_user

    return dependency
