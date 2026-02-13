from __future__ import annotations
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Column, JSON


def utc_now() -> datetime:
    return datetime.utcnow()


class Org(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=utc_now)


class User(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    org_id: Optional[UUID] = Field(default=None, index=True)
    sub: str = Field(index=True, unique=True)
    email: str
    name: str
    created_at: datetime = Field(default_factory=utc_now)


class OrgMembership(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    org_id: UUID = Field(index=True)
    user_id: UUID = Field(index=True)
    created_at: datetime = Field(default_factory=utc_now)


class Role(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    org_id: UUID = Field(index=True)
    name: str
    created_at: datetime = Field(default_factory=utc_now)


class Permission(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    key: str = Field(index=True, unique=True)
    description: str = ""


class RolePermission(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    org_id: UUID = Field(index=True)
    role_id: UUID = Field(index=True)
    permission_id: UUID = Field(index=True)


class UserRole(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    org_id: UUID = Field(index=True)
    user_id: UUID = Field(index=True)
    role_id: UUID = Field(index=True)


class Incident(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    org_id: UUID = Field(index=True)
    title: str
    status: str
    severity: str
    description: str = ""
    created_at: datetime = Field(default_factory=utc_now)


class IncidentSignal(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    org_id: UUID = Field(index=True)
    incident_id: UUID = Field(index=True)
    type: str
    payload: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utc_now)


class IncidentHypothesis(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    org_id: UUID = Field(index=True)
    incident_id: UUID = Field(index=True)
    summary: str
    confidence: float = 0.0
    created_at: datetime = Field(default_factory=utc_now)


class IncidentSuspectedChange(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    org_id: UUID = Field(index=True)
    incident_id: UUID = Field(index=True)
    source: str
    reference: str
    created_at: datetime = Field(default_factory=utc_now)


class RemediationAction(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    org_id: UUID = Field(index=True)
    incident_id: UUID = Field(index=True)
    title: str
    status: str
    details: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utc_now)


class Conversation(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    org_id: UUID = Field(index=True)
    incident_id: Optional[UUID] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=utc_now)


class Message(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    org_id: UUID = Field(index=True)
    conversation_id: UUID = Field(index=True)
    sender: str
    content: str
    created_at: datetime = Field(default_factory=utc_now)


class AssistantEvent(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    org_id: UUID = Field(index=True)
    event_type: str
    payload: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utc_now)


class RCAReport(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    org_id: UUID = Field(index=True)
    incident_id: UUID = Field(index=True)
    summary: str
    evidence: list[dict] = Field(default_factory=list, sa_column=Column(JSON))
    approved: bool = False
    created_at: datetime = Field(default_factory=utc_now)


class KBDocument(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    org_id: UUID = Field(index=True)
    title: str
    content: str
    created_at: datetime = Field(default_factory=utc_now)


class KGNode(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    org_id: UUID = Field(index=True)
    label: str
    node_type: str
    properties: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utc_now)


class KGEdge(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    org_id: UUID = Field(index=True)
    source_id: UUID = Field(index=True)
    target_id: UUID = Field(index=True)
    relation: str
    properties: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utc_now)


class AuditEvent(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    org_id: Optional[UUID] = Field(default=None, index=True)
    actor_user_id: Optional[UUID] = Field(default=None, index=True)
    event_type: str
    detail: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utc_now)
