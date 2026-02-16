from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.db.session import init_db, engine
from app.seed import seed_permissions, seed_roles, seed_sample_data
from app.db.models import Org
from sqlmodel import Session, select
from app.routers.opsmind import (
    identity,
    admin,
    governance,
    incidents,
    detect,
    correlate,
    impact,
    assistant,
    knowledge,
    graph,
    rca,
    remedy,
    approvals,
    actions,
    rollback,
    changeiq,
    risk,
    simulate,
    learn,
    insight,
)

settings = get_settings()

app = FastAPI(
    title="OpsMind API",
    description="Enterprise-safe AIOps platform API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)

    # Keep docs usable while preserving security hardening elsewhere.
    path = request.url.path
    is_docs_endpoint = (
        path.startswith("/docs")
        or path.startswith("/redoc")
        or path == "/openapi.json"
    )

    if is_docs_endpoint:
        response.headers[
            "Content-Security-Policy"
        ] = "default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; script-src 'self' 'unsafe-inline'"
    else:
        response.headers["Content-Security-Policy"] = "default-src 'self'"

    response.headers[
        "Strict-Transport-Security"
    ] = "max-age=63072000; includeSubDomains; preload"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=()"

    return response


@app.on_event("startup")
def on_startup():
    init_db()
    with Session(engine) as session:
        seed_permissions(session)
        orgs = session.exec(select(Org)).all()
        for org in orgs:
            seed_roles(session, org.id)
            seed_sample_data(session, org.id)


app.include_router(identity.router)
app.include_router(admin.router)
app.include_router(governance.router)
app.include_router(incidents.router)
app.include_router(detect.router)
app.include_router(correlate.router)
app.include_router(impact.router)
app.include_router(assistant.router)
app.include_router(knowledge.router)
app.include_router(graph.router)
app.include_router(rca.router)
app.include_router(remedy.router)
app.include_router(approvals.router)
app.include_router(actions.router)
app.include_router(rollback.router)
app.include_router(changeiq.router)
app.include_router(risk.router)
app.include_router(simulate.router)
app.include_router(learn.router)
app.include_router(insight.router)


@app.get("/")
def root():
    return {
        "message": "OpsMind API",
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
    }
