# Phase 1, Stage 0: Architecture (Backend and Data Layer)

Status: **draft for human review**. Documentation only; no code in this stage.

## 1. Scope

In scope (project plan, Phase 1): FastAPI app, health/readiness endpoints, SQLAlchemy + Alembic,
PostgreSQL models for jobs / reports / execution metadata, Qdrant collection and vector-search
operations, configuration, input validation, centralized error handling, **request rate limiting**, structured logging,
OpenTelemetry readiness, unit and integration tests.

Out of scope: MCP, embedding generation, LLM calls, agents, frontend, real OTel exporters
(Phases 2 to 6). Phase 1 creates the *seams* they plug into.

## 2. Package layout (modular monolith)

```
backend/app/
  main.py            app factory, lifespan (startup/shutdown), router wiring
  core/
    config.py        Settings (pydantic-settings), secrets loading
    logging.py       JSON logging, redaction filter, request-id context
    errors.py        AppError hierarchy + exception handlers
  api/
    routes/health.py   /health/live, /health/ready
    routes/jobs.py     job create/get/list (minimal; workflow wired in Phase 4)
    deps.py            FastAPI dependencies (db session, qdrant client, settings)
  schemas/           Pydantic request/response models (API contract)
  db/
    base.py          declarative base, naming conventions
    models.py        SQLAlchemy models
    session.py       async engine + session factory
  repositories/      DB access (jobs, reports, events); no business logic
  vector/
    client.py        Qdrant client factory
    store.py         collection setup, upsert, search (embedding-agnostic)
  services/          business logic (job lifecycle)
backend/alembic/     migrations
backend/tests/       unit/ and integration/
```

Rule: routes -> services -> repositories/vector store. Routes never touch SQLAlchemy directly.
Integrations are injected through FastAPI dependencies so tests can substitute them.

## 3. Key decisions

| Decision | Choice | Reason |
|---|---|---|
| DB driver / mode | SQLAlchemy 2.0 **async** + `psycopg` 3 | Avoids blocking the event loop; one driver for app and Alembic |
| Migrations | Alembic, **applied automatically on app startup in every mode** (same code path in dev, test, production) | No manual step; identical behavior everywhere. See 3b |
| Rate limiting | In-process per-client limiter, in scope for Phase 1 | No Redis allowed; see 3c |
| Dev infrastructure | Minimal `infra/docker/compose.dev.yml` (PostgreSQL + Qdrant only) | Needed for integration tests; Phase 8 replaces it with the full Compose setup |
| Primary keys | UUID (v4), server-independent | Safe to expose in URLs, no enumeration |
| Config | `pydantic-settings`; plain values from env, **secrets from files** via `secrets_dir` | Matches Section 4; same code in dev/Compose/K8s |
| DB URL | Built from host/port/name/user config + password from `database_password` secret file | Password never in a URL string in config or logs |
| Logging | stdlib `logging` + JSON formatter + redaction filter, `request_id` and (later) `trace_id` fields | No extra dependency; backend-agnostic |
| Qdrant | `qdrant-client` async; collection created idempotently at startup of a CLI/step, not per request | Keeps request path simple |
| Vector size / distance | Configured (`QDRANT_VECTOR_SIZE`, default 384, cosine) matching `all-MiniLM-L6-v2` | Final model chosen in Phase 3; config avoids a code change |
| Errors | Single JSON envelope `{error: {code, message, request_id}}`; no stack traces to clients | Section 6, Phase 5 and 8 requirements |
| Health | `/health/live` = process only; `/health/ready` = DB + Qdrant checks, 503 on failure | Acceptance criterion: health vs readiness are distinct |

## 3a. Runtime modes: dev, test, production

One plain (non-secret) setting, `APP_ENV` = `dev` | `test` | `production`, selects the mode.
It defaults to `dev`; an unknown value fails at startup. "Production" means the deployed
configuration (Compose / Kubernetes); it does not imply cloud resources (Section 4 cost rules).

| Concern | dev | test | production |
|---|---|---|---|
| Logging | DEBUG, readable console output | WARNING, JSON, captured by pytest | INFO, JSON, redaction on |
| API docs (`/docs`) | enabled | enabled | **disabled** |
| Secrets source | `./secrets/` | fake values injected by test fixtures; no real secret files read | `/run/secrets` (Compose / K8s) |
| Required secrets | only those for features in use | none | **all required secrets must exist, else startup fails** |
| PostgreSQL | local `agentops` database | separate `agentops_test` database, recreated per run | deployed database |
| Qdrant | local, collection `documentation_chunks` | in-memory client or `test_`-prefixed collection, deleted after run | deployed Qdrant, collection `documentation_chunks` |
| LLM / GitHub / external network | real calls allowed (free tier) | **disabled**; mocked clients only | real calls allowed |
| Telemetry exporters | off by default | off, forced | enabled by configuration |
| CORS | localhost origins | n/a | explicit allowlist, no wildcard |
| Error details to clients | generic (stack traces only in logs) | generic | generic |

Safety guards (fail at startup, not at first use):
- `test` refuses a database name that does not end in `_test`, so tests can never touch dev data.
- `test` refuses to construct real LLM or GitHub clients.
- `production` refuses debug flags, wildcard CORS, enabled `/docs`, and missing or placeholder
  (`replace-me`) secrets.
- `dev` never reads production secret locations unless `SECRETS_DIR` is set explicitly.

Config layout: one `Settings` class with per-mode defaults applied in a single place
(`core/config.py`), not scattered `if env == ...` checks through the code. Each mode's
differences are the table above and nothing else.

## 3b. Migrations on startup (all modes)

Startup runs `alembic upgrade head` programmatically before the app accepts traffic, the same
way in dev, test and production. Tests therefore exercise the real migrations, never
`create_all`.

- **Concurrency:** replicas may start together (Kubernetes). The runner takes a PostgreSQL
  advisory lock, so one instance migrates while the others wait, then all proceed.
- **Failure:** if the database is unreachable or a migration fails, the app does not become
  ready: startup fails with a logged error naming the migration, and `/health/ready` stays 503.
  It never serves traffic against an unmigrated schema.
- **Safety:** migrations must be backward compatible with the previous app version (add before
  remove) so rolling deploys stay safe. Destructive migrations are called out in review.
- **Overhead:** when already at head, the check is a single version lookup.

## 3c. Rate limiting (Phase 1)

Required by the security requirements and not deferred.

- **Mechanism:** token-bucket limiter in middleware, in process (no Redis or other new
  infrastructure). Keyed by client IP, taken from the connection, or from `X-Forwarded-For` only
  when a trusted proxy setting is enabled. The key is never used as a metric label or logged raw.
- **Tiers:** a stricter limit for job creation (the expensive endpoint, later backed by LLM calls)
  and a looser global limit for reads. Health endpoints are exempt.
- **Response:** HTTP 429 with the standard error envelope and a `Retry-After` header.
- **Also enforced:** maximum request body size and request timeouts.
- **Limit of the approach:** counters are per replica, so effective limits scale with replica
  count. This is acceptable for the demo scale and is documented. Limits are configuration values.
- **Modes:** enabled in all modes; test mode uses small limits so the behavior is testable.

## 4. Data flow (Phase 1)

1. Client creates a job with a repository URL and question (exact route and contract are defined in Stage 2).
2. Pydantic validates: repo URL must be `https://github.com/<owner>/<repo>` (public GitHub host
   only, normalized, no extra path/query); question length bounded.
3. Service creates `analysis_jobs` row (`status=queued`), logs an `execution_events` row.
4. Response returns job id and status. In Phase 1 nothing processes the job; Phase 4 attaches
   the LangGraph workflow to the same lifecycle.
5. `GET /api/v1/jobs/{id}` returns status, report (if any), and events.

Job states: `queued -> running -> completed | failed | timed_out`. Transitions are enforced in
the service layer.

## 5. Data model (summary; detailed in Stage 1)

- `analysis_jobs`: id, repo_url, question, status, error_code, created/started/finished timestamps.
- `reports`: id, job_id (FK, unique), summary, findings (JSONB), recommendations (JSONB),
  sources (JSONB), created_at.
- `execution_events`: id, job_id (FK), sequence, event_type, component (agent/mcp/rag/llm),
  status, duration_ms, metadata (JSONB, no prompts or source content), created_at.
- Qdrant `documentation_chunks` collection: vector + payload (source_url, section_title,
  text, chunk_index, doc_version).

No API secrets are stored in PostgreSQL or Qdrant.

## 6. Failure modes

| Failure | Behavior |
|---|---|
| PostgreSQL down at startup | App starts; `/health/live` OK, `/health/ready` 503; DB-backed routes return 503 `dependency_unavailable` |
| Qdrant down | Same; readiness reports which dependency failed (name only, no connection details) |
| Invalid URL / question | 422 with field-level messages |
| Unknown job id | 404 `not_found` |
| Unexpected exception | Logged with stack trace and request_id; client gets 500 `internal_error` |
| Missing required secret | Fail fast at startup with the *name* of the missing secret, never its value |
| Pool exhaustion / slow DB | Bounded pool and statement/connection timeouts; surfaced as 503 |
| Migration fails or lock not acquired in time | Startup aborts with a logged error; not ready; no traffic served |
| Rate limit exceeded | 429 `rate_limited` with `Retry-After` |

## 7. Observability readiness

- Request-id middleware; id appears in logs, error envelopes, and response header `X-Request-ID`.
- Log formatter reserves `trace_id` / `span_id` fields (populated in Phase 6 when OTel is on).
- Metrics, tracing and exporters are **not** added in Phase 1. Code is structured so Phase 6
  instrumentation wraps routes/services without touching business logic.
- Redaction filter masks secret values and sensitive keys (authorization, api_key, password, token).
- Never log: prompts, repository file contents, secret values, full request bodies.

## 8. Testing approach (detailed in Stage 5)

- Unit: settings/secrets loading, URL validation, state transitions, error mapping, log redaction.
- Integration: repositories and migrations against real PostgreSQL; vector store against real Qdrant.
- API tests with `httpx` + dependency overrides.
- Integration tests are marked and need local Postgres + Qdrant (Docker). No paid services, no LLM.

## 9. Cost impact

$0. PostgreSQL and Qdrant run locally in Docker. No cloud resources, no hosted services.

## 10. Dependencies to add (pinned in Stage 4, not before)

`fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`, `sqlalchemy[asyncio]`, `psycopg[binary,pool]`,
`alembic`, `qdrant-client`; dev: `httpx`. Each has a direct Phase 1 purpose.

## 11. Resolved decisions (from review)

1. `infra/docker/compose.dev.yml` with PostgreSQL and Qdrant only is approved; Phase 8 replaces it.
2. The exact API surface for jobs is decided in Stage 2 (API and interface design), not here.
3. Migrations run automatically at startup in every mode, with no extra step (see 3b).
4. Rate limiting is in Phase 1 scope (see 3c).
5. Embedding default stays 384 dimensions with cosine distance; revisit in Phase 3.

## 12. Open questions for the reviewer

1. Rate limit defaults (requests per minute for job creation and for reads)? Proposal: 5/min for
   job creation and 60/min for reads per client, as configuration values.
2. Is per-replica rate limiting acceptable, given Redis is excluded by project rules?
