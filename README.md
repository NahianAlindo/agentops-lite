# AgentOps Lite

Multi-agent application that investigates a public GitHub repository and produces an
evidence-based engineering report. Built to demonstrate LangGraph orchestration, a custom
MCP server, RAG, observability (OpenTelemetry, Prometheus, Grafana, Datadog, Sentry), CI/CD, Terraform and
Kubernetes autoscaling, at $0 recurring cost.

**Status:** Phase 0 (repository setup) complete. See [docs/checklist.md](docs/checklist.md).

## Layout

| Path | Purpose |
|---|---|
| `backend/` | FastAPI app, agents, MCP server, RAG (Python 3.12, uv, Ruff, pytest) |
| `frontend/` | React + TypeScript UI (Vite) |
| `infra/docker`, `infra/k8s`, `infra/terraform` | Containers, manifests, IaC (later phases) |
| `secrets/` | Local secret files (gitignored, never committed); see [docs/secrets.md](docs/secrets.md) |
| `monitoring/` | OpenTelemetry Collector, Prometheus, Tempo, Grafana and Datadog configuration (Phases 1b and 6) |
| `docs/` | Architecture, checklist, observability plan |

## Local development

```bash
# create the secret files listed in docs/secrets.md (gitignored)

# backend
cd backend
uv sync
uv run ruff check . && uv run ruff format --check .
uv run pytest

# frontend
cd frontend
npm install
npm run dev        # http://localhost:5173
npm run build      # typecheck + production build
```

## Docs

- [Architecture and phase boundaries](docs/architecture.md)
- [Implementation checklist](docs/checklist.md)
- [Observability plan](docs/observability.md)
- [Secrets](docs/secrets.md)
