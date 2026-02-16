# OpsMind (LLM App+ for SRE/RCA)

Cloud-portable monorepo (GCP-first, AWS-ready) with ports/adapters design.

## Structure
- `apps/api`: FastAPI backend + orchestrator entrypoint
- `apps/web`: minimal portal chat UI served by backend
- `packages/contracts`: Pydantic v2 schemas
- `packages/orchestrator`: deterministic workflow engine
- `packages/tools`: tool registry + deterministic stubs
- `packages/storage`: state/transcript/tool result ports + memory and redis/postgres adapters
- `packages/common`: structured logging and tracing hooks
- `deploy/docker`: docker assets

## Run locally (memory mode)
```bash
cd opsmind
pip install -r apps/api/requirements.txt
uvicorn apps.api.app.main:app --reload --host 0.0.0.0 --port 8000
```
Open `http://localhost:8000`.

## Run with Redis + Postgres
```bash
cd opsmind/deploy/docker
docker compose up --build
```
Open `http://localhost:8000`.

## API
- `POST /v1/chat/send`
- `GET /v1/chat/conversations/{conversation_id}`
- `POST /v1/chat/feedback` (stub)

Headers supported for tenant routing: `X-Org-Id`, `X-Project-Id`.

## Testing
```bash
cd opsmind
PYTHONPATH=packages/contracts:packages/orchestrator:packages/tools:packages/storage:packages/common pytest -q
```
