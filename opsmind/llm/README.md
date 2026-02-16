# OpsMind LLM Abstraction

`opsmind.llm` is a provider-agnostic library for OpenAI, Anthropic, and Gemini/Vertex routing in the OpsMind FastAPI backend.

## Local setup (.env)

```env
LLM_PROVIDERS_ENABLED=["openai","anthropic","gemini"]
LLM_DEFAULT_PROVIDER=gemini

OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
GOOGLE_API_KEY=...
# Vertex alternative:
VERTEX_PROJECT=my-project
VERTEX_LOCATION=us-central1

REQUEST_TIMEOUT_MS=30000
MAX_RETRIES=2
MAX_COST_USD_PER_REQUEST=1.0
MAX_TOKENS_PER_REQUEST=32000
```

## Run tests

```bash
pytest opsmind/llm/tests -q
```

## Routing and fallback

- Routes by logical model tier (`fast`, `balanced`, `reasoning`) via provider/model mapping.
- Applies policy enforcement before request dispatch.
- Falls back on retryable provider errors (timeouts, rate limits, transient outages).
- Hard-fails on invalid request/auth/budget policy errors.
- Includes simple latency-aware rerouting using rolling provider latency windows.

## Tool normalization

All providers normalize tool calls into:

- `ToolSpec` for definitions (`name`, `description`, `json_schema`, `version`)
- `ToolCall` for execution (`id`, `name`, `arguments` dict)

This keeps business logic provider-independent and agent-ready.

## Security notes

- Prompts are not logged by default (only metadata and message lengths/tokens).
- API keys and auth headers are never logged.
- Secret manager interface supports env-based local dev and a GCP placeholder implementation.
- Optional PII redaction hook can sanitize emails/phone-like strings in logs/traces.

## Add a new provider

1. Create `providers/<provider>_provider.py` implementing `LLMProvider`.
2. Map provider payloads to `LLMRequest` / `LLMResponse` and `ToolCall`.
3. Add model mappings + pricing in config/cost.
4. Register provider in `LLMRouter`.
5. Add normalization, fallback, and error mapping tests.

## Caching

The optional in-memory cache stores deterministic requests (`metadata.cacheable=true`, no tools). For production scale, replace with Redis-backed cache.
