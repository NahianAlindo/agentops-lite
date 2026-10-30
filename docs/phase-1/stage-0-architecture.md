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
    ratelimit.py     RateLimiter interface, Redis and in-memory implementations, middleware
  api/
    routes/health.py   /health/live, /health/ready
    routes/jobs.py     job create/get/list (minimal; workflow wired in Phase 4)
    deps.py            FastAPI dependencies (db session, qdrant client, settings)
  schemas/           Pydantic request/response models (API contract)
  db/
    base.py          declarative base, naming conventions
    models.py        SQLAlchemy models
    session.py       async engine + session factory
    migrate.py       startup migration runner (advisory lock, bounded retry)
  repositories/      DB access (jobs, reports, events); no business logic
  vector/
    client.py        Qdrant client factory
    store.py         collection setup, upsert, search (embedding-agnostic)
  services/          business logic (job lifecycle)
backend/alembic/     migrations
backend/tests/       unit/ and integration/
infra/docker/compose.dev.yml   PostgreSQL, Qdrant, Redis for local development and tests
```

Rule: routes -> services -> repositories/vector store. Routes never touch SQLAlchemy directly.
Integrations are injected through FastAPI dependencies so tests can substitute them.

## 3. Key decisions

| Decision | Choice | Reason |
|---|---|---|
| DB driver / mode | SQLAlchemy 2.0 **async** + `psycopg` 3 | Avoids blocking the event loop; one driver for app and Alembic |
| Migrations | Alembic, **applied automatically on app startup in every mode** (same code path in dev, test, production) | No manual step; identical behavior everywhere. See 3b |
| Rate limiting | Redis-backed limiter shared across replicas, with in-memory fallback; in scope for Phase 1 | Counters must be global across replicas; see 3c |
| Dev infrastructure | Minimal `infra/docker/compose.dev.yml` (PostgreSQL, Qdrant and Redis) | Needed for integration tests; Phase 8 replaces it with the full Compose setup |
| Primary keys | UUID (v4), server-independent | Safe to expose in URLs, no enumeration |
| Config | `pydantic-settings`; plain values from env, **secrets from files** via `secrets_dir` | Matches Section 4; same code in dev/Compose/K8s |
| Secrets directory (dev) | Default resolved from the repository root (`<repo>/secrets`), not the working directory | The app runs from `backend/` while `secrets/` is at the repo root |
| DB URL | Built from host/port/name/user config + password from `database_password` secret file | Password never in a URL string in config or logs |
| Logging | stdlib `logging` + JSON formatter + redaction filter, `request_id` and (later) `trace_id` fields | No extra dependency; backend-agnostic |
| Qdrant | `qdrant-client` async; collection created idempotently at startup of a CLI/step, not per request | Keeps request path simple |
| Vector size / distance | Configured (`QDRANT_VECTOR_SIZE`, default 384, cosine) matching `all-MiniLM-L6-v2` | Final model chosen in Phase 3; config avoids a code change |
| Errors | Single JSON envelope `{error: {code, message, request_id}}`; no stack traces to clients | Section 6, Phase 5 and 8 requirements |
| Health | `/health/live` = process only; `/health/ready` = PostgreSQL and Qdrant required (503 if either fails), Redis reported as `degraded` without failing readiness | Acceptance criterion: health vs readiness are distinct; rate limiting has a fallback (3c) |

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
| Redis | local container | unit tests: in-memory limiter; integration tests: real local Redis, separate DB index, flushed per run | deployed Redis |
| Qdrant | local, collection `documentation_chunks` | unit tests: in-memory client; integration tests: real local Qdrant, `test_`-prefixed collection, deleted after run | deployed Qdrant, collection `documentation_chunks` |
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
- **Failure (fail fast):** if the database is unreachable, the runner retries for a bounded,
  configurable window (default 30 s). If it still cannot connect, or a migration fails, or the
  lock is not acquired in time, the process logs the error (naming the migration, never
  connection secrets) and exits non-zero. Docker Compose or Kubernetes restarts it. It never
  serves traffic against an unmigrated schema. `/health/ready` returning 503 applies only when a
  dependency is lost *after* a successful startup.
- **Safety:** migrations must be backward compatible with the previous app version (add before
  remove) so rolling deploys stay safe. Destructive migrations are called out in review.
- **Overhead:** when already at head, the check is a single version lookup.

## 3c. Rate limiting (Phase 1)

Required by the security requirements and not deferred. Counters are shared across replicas, so
a client cannot multiply its limit by hitting different pods.

- **Store:** Redis, used **only** for rate-limit counters in this phase (not caching, queues, or
  job state). Redis OSS runs as a local container ($0). Valkey is a protocol-compatible drop-in if
  the Redis license is a concern; no code change would be needed. No hosted Redis (it costs money).
- **Algorithm:** fixed or sliding window counter via an atomic Lua script / `INCR` + `EXPIRE`, so
  concurrent replicas cannot race. Implemented in middleware behind a small `RateLimiter`
  interface so the store is swappable.
- **Key:** client IP from the connection, or from `X-Forwarded-For` only when a trusted-proxy
  setting is enabled. Stored as a hash with a short TTL; never logged raw and never a metric label.
- **Tiers:** stricter for job creation (later backed by LLM calls), looser for reads. Health
  endpoints are exempt. Defaults (approved): **5 requests/min for job creation, 60/min for reads**,
  as configuration values.
- **Response:** HTTP 429 with the standard error envelope and a `Retry-After` header.
- **Redis unavailable:** the limiter degrades to a per-process in-memory limiter and logs a
  warning; the app keeps working. It does not fail open to unlimited traffic and does not block
  requests. Readiness reports Redis as degraded but not failed, because rate limiting is not
  required for correctness.
- **Also enforced:** maximum request body size and request timeouts.
- **Modes:** enabled in all modes; test mode uses small limits so the behavior is testable.
- **Future:** an ingress-level limit in Phase 10 as an additional outer layer (approved), not a
  replacement for the application limiter.

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
  status, duration_ms, details (JSONB, no prompts or source content; not named `metadata`,
  which SQLAlchemy reserves on models), created_at.
- Qdrant `documentation_chunks` collection: vector + payload (source_url, section_title,
  text, chunk_index, doc_version).

No API secrets are stored in PostgreSQL or Qdrant.

## 6. Failure modes

| Failure | Behavior |
|---|---|
| PostgreSQL down at startup | Migration runner retries for the bounded window, then the process exits non-zero; the orchestrator restarts it; no traffic served (3b) |
| PostgreSQL lost after startup | `/health/live` OK, `/health/ready` 503; DB-backed routes return 503 `dependency_unavailable` |
| Qdrant down | App still starts; `/health/ready` 503 naming the dependency (name only, no connection details); Qdrant-backed operations return 503 |
| Invalid URL / question | 422 with field-level messages |
| Unknown job id | 404 `not_found` |
| Unexpected exception | Logged with stack trace and request_id; client gets 500 `internal_error` |
| Missing required secret | Fail fast at startup with the *name* of the missing secret, never its value |
| Pool exhaustion / slow DB | Bounded pool and statement/connection timeouts; surfaced as 503 |
| Migration fails or lock not acquired in time | Startup aborts with a logged error; not ready; no traffic served |
| Rate limit exceeded | 429 `rate_limited` with `Retry-After` |
| Redis down | Limiter falls back to in-memory per process; warning logged; readiness shows `degraded` for Redis, app stays ready |

## 7. Observability readiness

- Request-id middleware; id appears in logs, error envelopes, and response header `X-Request-ID`.
- Log formatter reserves `trace_id` / `span_id` fields (populated in Phase 1b when OpenTelemetry is enabled).
- Metrics, tracing and exporters are **not** added in Phase 1; they arrive in Phase 1b (the
  early observability slice). Code is structured so that instrumentation wraps routes and
  services without touching business logic.
- Redaction filter masks secret values and sensitive keys (authorization, api_key, password, token).
- Never log: prompts, repository file contents, secret values, full request bodies.

## 8. Testing approach (detailed in Stage 5)

- Unit: settings/secrets loading, URL validation, state transitions, error mapping, log redaction.
- Integration: repositories and migrations against real PostgreSQL; vector store against real
  Qdrant; rate limiter against real Redis.
- API tests with `httpx` + dependency overrides.
- Integration tests are marked and need local PostgreSQL, Qdrant and Redis (Docker). No paid
  services, no LLM.

## 9. Cost impact

$0. PostgreSQL, Qdrant and Redis run locally in Docker (Redis OSS and Valkey are free; no hosted Redis). No cloud resources, no hosted services.

## 10. Dependencies

Definition-only libraries (`pydantic`, `pydantic-settings`, `sqlalchemy[asyncio]`) are added in
Stage 1, because models cannot be written without them. Everything else is added in Stage 4.
All are pinned to compatible ranges and locked in `uv.lock`.

`fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`, `sqlalchemy[asyncio]`, `psycopg[binary,pool]`,
`alembic`, `qdrant-client`, `redis` (async client); dev: `httpx`. Each has a direct Phase 1 purpose.

## 11. Resolved decisions (from review)

1. `infra/docker/compose.dev.yml` is approved; Phase 8 replaces it.
2. The exact API surface for jobs is decided in Stage 2 (API and interface design), not here.
3. Migrations run automatically at startup in every mode, with no extra step (see 3b).
4. Rate limiting is in Phase 1 scope (see 3c). Defaults approved: 5/min job creation, 60/min reads.
5. Embedding default stays 384 dimensions with cosine distance; revisit in Phase 3.
6. Redis is approved, scoped to rate limiting only, local container, in-memory fallback.
   This is an exception to the "no Redis" default; the project plan is updated accordingly.
7. Ingress-level rate limiting is wanted later (Phase 10).

## 12. Open questions for the reviewer

None outstanding. Review the design and approve to start Stage 1.
