# Secrets

Secrets are files, not environment variables or `.env` files. Each file holds only the value
(no quotes, no `KEY=` prefix). The `secrets/` directory is gitignored and must never be committed.

A secret is required only when the feature that uses it is enabled. In production mode, startup
fails if a secret required by an enabled feature is missing or still a placeholder.

| File | Required when | Purpose |
|---|---|---|
| `database_password` | always | PostgreSQL password |
| `redis_password` | Redis is configured | Redis authentication for rate-limit counters |
| `qdrant_api_key` | Qdrant has authentication enabled | Qdrant access outside local development |
| `groq_api_key` | the agent workflow is enabled (Phase 4 onward) | Groq LLM (free tier) |
| `gemini_api_key` | Gemini is selected as the LLM provider | Alternative LLM |
| `github_token` | optional | Read-only token to raise the GitHub API rate limit |
| `datadog_api_key` | the Datadog route is enabled | Hosted observability |
| `sentry_dsn` | Sentry is enabled | Error tracking |

Where the app looks:

- dev: `secrets/` at the repository root, resolved independently of the working directory
  (override with `SECRETS_DIR`)
- Docker Compose: Compose `secrets:` mounted at `/run/secrets`
- Kubernetes: a Secret mounted as a volume at `/run/secrets`
- test: no secret files are read; tests inject fake values

Non-secret settings (log level, Qdrant URL, agent limits) are ordinary configuration.
