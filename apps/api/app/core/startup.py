"""Application startup tasks."""
from sqlmodel import Session, select

from app.db.models import Org
from app.db.session import engine
from app.seed import seed_permissions, seed_roles, seed_sample_data


def init_application() -> None:
    """Initialize database and seed initial data."""
    from app.db.session import init_db
    
    init_db()
    
    with Session(engine) as session:
        seed_permissions(session)
        orgs = session.exec(select(Org)).all()
        for org in orgs:
            seed_roles(session, org.id)
            seed_sample_data(session, org.id)
