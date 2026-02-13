from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from app.core.security import CurrentUser, require
from app.db.session import get_session
from app.db.models import KGNode, KGEdge
from app.services.audit import record_audit_event

router = APIRouter(prefix="/opsmind/graph", tags=["graph"])


class KGNodeCreate(BaseModel):
    label: str
    node_type: str
    properties: dict = {}


@router.get("/nodes")
def list_nodes(
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(require("opsmind.graph.read")),
):
    nodes = session.exec(select(KGNode).where(KGNode.org_id == current_user.org_id)).all()
    return [
        {
            "id": str(node.id),
            "label": node.label,
            "node_type": node.node_type,
            "properties": node.properties,
        }
        for node in nodes
    ]


@router.get("/edges")
def list_edges(
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(require("opsmind.graph.read")),
):
    edges = session.exec(select(KGEdge).where(KGEdge.org_id == current_user.org_id)).all()
    return [
        {
            "id": str(edge.id),
            "source_id": str(edge.source_id),
            "target_id": str(edge.target_id),
            "relation": edge.relation,
        }
        for edge in edges
    ]


@router.post("/nodes")
def create_node(
    payload: KGNodeCreate,
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(require("opsmind.graph.write")),
):
    node = KGNode(
        org_id=current_user.org_id,
        label=payload.label,
        node_type=payload.node_type,
        properties=payload.properties,
    )
    session.add(node)
    session.commit()
    record_audit_event(
        session,
        "graph.node.created",
        {"node_id": str(node.id)},
        org_id=current_user.org_id,
        actor_user_id=current_user.id,
    )
    return {"id": str(node.id)}
