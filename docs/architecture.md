# Architecture

Modular monolith: React frontend -> FastAPI backend -> LangGraph workflow.
The MCP server (read-only GitHub tools) is logically separate from the agent workflow.
PostgreSQL holds jobs, reports and execution metadata; Qdrant holds embeddings and chunks.
LLM inference uses Groq's free tier (Gemini optional). Embeddings are generated locally.

```
React UI -> FastAPI -> LangGraph orchestrator
                         |- Repository Analyst   -> MCP client -> MCP server -> GitHub (public, read-only)
                         |- Documentation Researcher -> RAG -> Sentence Transformers + Qdrant
                         `- Engineering Reviewer (bounded iterations)
FastAPI -> PostgreSQL (SQLAlchemy + Alembic)
All components -> OpenTelemetry (OTLP) -> optional Datadog Agent -> Datadog (traces, metrics, logs)
Unhandled exceptions -> optional Sentry (errors only, linked by trace id)
```

## Key decisions

- **Python 3.12** (pinned): the machine default is 3.14, which risks missing wheels for
  torch / sentence-transformers. 3.12 is installed via uv.
- **uv** for Python dependency management; **npm** for the frontend.
- **Vite** for the frontend build.
- Runtime dependencies are added in the phase that needs them, not up front.
- **File-based secrets, no `.env`:** secrets are files read from a secrets directory (local `secrets/`, Compose secrets, Kubernetes Secret volumes), so the app code is identical everywhere. Azure Key Vault is deferred until cost review.
- No Redis, Celery, Kafka or Django (per project rules).

## Phase boundaries

Development proceeds in phases 0-11 (see [checklist](checklist.md)). Each phase is completed, tested and summarized before the next starts, and each is delivered through a staged, reviewed pull request workflow.
