# OpsMind API

This is the main OpsMind API application providing enterprise-safe AIOps platform endpoints.

## Structure

- `app/main.py` - Main FastAPI application entry point
- `app/core/` - Core configuration, security, middleware, and startup logic
- `app/db/` - Database models and session management
- `app/routers/` - API route handlers organized by domain
- `app/services/` - Business logic services

## API Endpoints

All endpoints are prefixed with `/opsmind/{domain}/`:
- `/opsmind/identity/*` - User identity and permissions
- `/opsmind/incidents/*` - Incident management
- `/opsmind/assistant/*` - AI assistant chat
- `/opsmind/knowledge/*` - Knowledge base management
- And more...

## Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI Schema: `http://localhost:8000/openapi.json`

## Note on Alternative Implementation

There is also an alternative API implementation in `opsmind/apps/api/` which provides chat/orchestrator functionality with `/v1/chat/*` endpoints. That implementation is separate and uses a different architecture with orchestrator services.
