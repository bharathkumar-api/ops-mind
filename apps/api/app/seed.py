from sqlmodel import Session, select
from app.db.models import (
    Permission,
    Role,
    RolePermission,
    KBDocument,
    KGNode,
    KGEdge,
    Incident,
    RCAReport,
)

PERMISSIONS = [
    "opsmind.identity.read",
    "opsmind.identity.permissions.read",
    "opsmind.admin.users.manage",
    "opsmind.admin.roles.manage",
    "opsmind.governance.audit.read",
    "opsmind.governance.export",
    "opsmind.incidents.read",
    "opsmind.incidents.write",
    "opsmind.incidents.admin",
    "opsmind.detect.read",
    "opsmind.detect.write",
    "opsmind.correlate.read",
    "opsmind.correlate.run",
    "opsmind.impact.read",
    "opsmind.impact.write",
    "opsmind.rca.read",
    "opsmind.rca.generate",
    "opsmind.rca.approve",
    "opsmind.assistant.read",
    "opsmind.assistant.write",
    "opsmind.assistant.admin",
    "opsmind.knowledge.read",
    "opsmind.knowledge.write",
    "opsmind.knowledge.admin",
    "opsmind.graph.read",
    "opsmind.graph.write",
    "opsmind.graph.admin",
    "opsmind.remedy.propose",
    "opsmind.approvals.approve",
    "opsmind.actions.execute",
    "opsmind.rollback.execute",
    "opsmind.changeiq.read",
    "opsmind.changeiq.write",
    "opsmind.risk.read",
    "opsmind.risk.run",
    "opsmind.simulate.run",
    "opsmind.learn.write",
    "opsmind.insight.read",
]

ROLE_SEEDS = {
    "owner": "all",
    "admin": "all",
    "editor": [
        "opsmind.incidents.read",
        "opsmind.incidents.write",
        "opsmind.detect.read",
        "opsmind.detect.write",
        "opsmind.correlate.read",
        "opsmind.correlate.run",
        "opsmind.impact.read",
        "opsmind.impact.write",
        "opsmind.assistant.read",
        "opsmind.assistant.write",
        "opsmind.rca.generate",
        "opsmind.remedy.propose",
    ],
    "viewer": [
        "opsmind.incidents.read",
        "opsmind.detect.read",
        "opsmind.correlate.read",
        "opsmind.impact.read",
        "opsmind.assistant.read",
        "opsmind.rca.read",
        "opsmind.knowledge.read",
        "opsmind.graph.read",
        "opsmind.insight.read",
    ],
}


def seed_permissions(session: Session) -> None:
    existing = session.exec(select(Permission)).all()
    if existing:
        return
    for key in PERMISSIONS:
        session.add(Permission(key=key, description=key))
    session.commit()


def seed_roles(session: Session, org_id) -> None:
    existing = session.exec(select(Role).where(Role.org_id == org_id)).all()
    if existing:
        return
    permissions = {perm.key: perm for perm in session.exec(select(Permission)).all()}
    for role_name, perms in ROLE_SEEDS.items():
        role = Role(org_id=org_id, name=role_name)
        session.add(role)
        session.commit()
        session.refresh(role)
        if perms == "all":
            for perm in permissions.values():
                session.add(RolePermission(org_id=org_id, role_id=role.id, permission_id=perm.id))
        else:
            for perm_key in perms:
                perm = permissions.get(perm_key)
                if perm:
                    session.add(RolePermission(org_id=org_id, role_id=role.id, permission_id=perm.id))
        session.commit()


def seed_sample_data(session: Session, org_id) -> None:
    if session.exec(select(KBDocument).where(KBDocument.org_id == org_id)).first():
        return
    session.add(KBDocument(org_id=org_id, title="RCA Playbook", content="Follow evidence, correlate signals, validate change records."))
    service_node = KGNode(org_id=org_id, label="payments-api", node_type="service", properties={"tier": "backend"})
    db_node = KGNode(org_id=org_id, label="postgres-cluster", node_type="database", properties={"tier": "data"})
    session.add(service_node)
    session.add(db_node)
    session.commit()
    session.refresh(service_node)
    session.refresh(db_node)
    session.add(KGEdge(org_id=org_id, source_id=service_node.id, target_id=db_node.id, relation="depends_on", properties={}))
    incident = Incident(org_id=org_id, title="Payments latency spike", status="open", severity="high", description="Latency regression detected.")
    session.add(incident)
    session.commit()
    session.refresh(incident)
    session.add(RCAReport(
        org_id=org_id,
        incident_id=incident.id,
        summary="Root cause tied to database saturation after deployment.",
        evidence=[{"source": "metrics", "detail": "DB CPU 95%"}, {"source": "changeiq", "detail": "Deploy 2024.10.12"}],
        approved=False,
    ))
    session.commit()
