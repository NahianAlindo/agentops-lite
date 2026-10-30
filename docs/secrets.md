# Secrets

Secrets are files, not environment variables or `.env` files. Each file holds only the value
(no quotes, no `KEY=` prefix). The `secrets/` directory is gitignored and must never be committed.

| File | Required | Purpose |
|---|---|---|
| `groq_api_key` | yes | Groq LLM (free tier) |
| `database_password` | yes | PostgreSQL password |
| `github_token` | no | Read-only token to raise the GitHub API rate limit |
| `gemini_api_key` | no | Alternative LLM |
| `sentry_dsn` | no | Error tracking |
| `datadog_api_key` | no | Hosted observability |

Where the app looks:

- dev: `./secrets/` (override with `SECRETS_DIR`)
- Docker Compose: Compose `secrets:` mounted at `/run/secrets`
- Kubernetes: a Secret mounted as a volume at `/run/secrets`
- test: no secret files are read; tests inject fake values

Optional secrets may be absent; the matching feature is then disabled.
Non-secret settings (log level, Qdrant URL, agent limits) are ordinary configuration.
