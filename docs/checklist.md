# Implementation checklist

- [x] Phase 0: Repository setup and planning
- [ ] Phase 1: Backend and data layer: FastAPI app; health and readiness endpoints; SQLAlchemy + Alembic with migrations on startup (advisory lock, fail fast); PostgreSQL models for jobs, reports and execution events; Qdrant collection and vector search; dev, test and production modes; file-based secrets; input validation and centralized errors; Redis-backed rate limiting with in-memory fallback, body-size limits and timeouts; structured JSON logging with redaction and request ids; OpenTelemetry seams; `infra/docker/compose.dev.yml` (PostgreSQL, Qdrant, Redis); unit and integration tests
- [ ] Phase 1b (Datadog slice, early): verify Datadog access and limits; OpenTelemetry traces, metrics and logs from the API through an OpenTelemetry Collector to Datadog; API dashboard and one monitor
- [ ] Phase 2: MCP server and client
- [ ] Phase 3: RAG pipeline
- [ ] Phase 4: Multi-agent workflow (LangGraph)
- [ ] Phase 4b (Datadog slice, evidence): agent, MCP, RAG and LLM spans and metrics in Datadog; workflow dashboard; controlled failure demonstration; store screenshots and a trace walkthrough in docs
- [ ] Phase 5: Frontend and API integration
- [ ] Phase 6 (remainder after 1b and 4b): local route (Prometheus, Tempo, Grafana dashboards), optional Sentry for errors, redaction hardening, infrastructure metrics, full observability docs
- [ ] Phase 7: Testing and reliability
- [ ] Phase 8: Docker and local deployment (FastAPI, PostgreSQL, Qdrant, Redis; optional Compose profiles: `observability-local`, `observability-datadog`, and `quality` for SonarQube Community Build)
- [ ] Phase 9: CI/CD (GitHub Actions) with PostgreSQL, Qdrant and Redis service containers; static analysis with SonarQube, quality gate as a required check
- [ ] Phase 10: Terraform and Kubernetes (local first; AKS only with explicit approval)
- [ ] Phase 11: Public demo and documentation

## Known risks

- Python 3.14 default vs ML wheel availability (mitigated: pinned to 3.12).
- Groq free-tier rate limits: needs caching, bounded iterations, no blind retries.
- GitHub unauthenticated API rate limit (60/hr): optional read-only token, caching.
- Embedding model download size (first run); keep the model small.
- Prompt injection from repository content and docs: treat as untrusted.

## Code quality tooling: SonarQube Cloud

- **Primary:** SonarQube Cloud (sonarcloud.io) free plan, as used on the hindcast-lakehouse
  project. The repository is public, which the free plan requires. Organization `nahianalindo`,
  project key `NahianAlindo_agentops-lite`.
- **Setup:** import the repository from the SonarQube Cloud dashboard. Automatic analysis needs no
  scanner config or token. It does not ingest test coverage, so if coverage tracking is wanted,
  Phase 9 adds CI-based analysis (a GitHub Actions scan step with a `SONAR_TOKEN` secret).
- **Quality gate:** once the project exists, add the SonarQube Cloud check as a required status
  check on `main` (Phase 9).
- **Optional local:** SonarQube Community Build in an on-demand Docker Compose `quality` profile
  (Phase 8) for offline scans. It needs about 2 GB of RAM and, on Windows with WSL2, a raised
  `vm.max_map_count`. It analyzes only the main branch.
- **Limits:** re-check the free plan's current limits before relying on it. No paid plan will be
  enabled. No source leaves the machine beyond what the public repository already exposes.
- **Complements, does not replace:** Ruff and pytest remain the primary checks.
