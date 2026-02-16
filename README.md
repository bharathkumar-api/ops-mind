# OpsMind

OpsMind is an enterprise-grade AIOps platform that detects incidents, reasons about root causes, and executes safe remediation within policy.

## Monorepo Layout
```
apps/web  # Next.js frontend
apps/api  # FastAPI backend
packages  # Shared packages
archive/legacy-opsmind # Archived legacy prototype monorepo (not used by current app)
```

## Repository Cleanup Notes

This repository previously included a second nested monorepo at `opsmind/` that duplicated
`apps/` and `packages/` concepts. To make the project layout clearer, that legacy code has
been moved to `archive/legacy-opsmind/`.

## Local Development
1. Copy `.env.example` to `.env` and adjust if needed.
2. Run `docker compose up --build`.
3. Visit `http://localhost:3000` for the web UI and `http://localhost:8000/docs` for API docs.

## Seed Data
On startup, the API seeds permissions, roles, a sample incident with RCA, and a starter knowledge base + graph for the first org.
