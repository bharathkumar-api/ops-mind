"""OpsMind API main application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.middleware import security_headers_middleware
from app.core.startup import init_application
from app.routers import register_routers

settings = get_settings()

# Create FastAPI application
app = FastAPI(
    title="OpsMind API",
    description="Enterprise-safe AIOps platform API",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security headers middleware
app.middleware("http")(security_headers_middleware)

# Initialize application on startup
@app.on_event("startup")
def on_startup():
    """Initialize database and seed data on application startup."""
    init_application()

# Register all routers
register_routers(app)
