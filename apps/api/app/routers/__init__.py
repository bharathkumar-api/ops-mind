"""Router registry for all OpsMind API endpoints."""

from app.routers.opsmind import (
    actions,
    admin,
    approvals,
    assistant,
    chat,
    changeiq,
    correlate,
    detect,
    governance,
    graph,
    identity,
    impact,
    incidents,
    insight,
    knowledge,
    learn,
    rca,
    remedy,
    risk,
    rollback,
    simulate,
)


def register_routers(app) -> None:
    """Register all OpsMind routers with the FastAPI application."""
    routers = [
        identity.router,
        admin.router,
        governance.router,
        incidents.router,
        detect.router,
        correlate.router,
        impact.router,
        assistant.router,
        knowledge.router,
        graph.router,
        rca.router,
        remedy.router,
        approvals.router,
        actions.router,
        rollback.router,
        changeiq.router,
        risk.router,
        simulate.router,
        learn.router,
        insight.router,
        chat.router,
    ]
    
    for router in routers:
        app.include_router(router)
