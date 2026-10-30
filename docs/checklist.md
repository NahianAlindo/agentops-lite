# Implementation checklist

- [x] Phase 0: Repository setup and planning
- [ ] Phase 1: Backend and data layer (FastAPI, SQLAlchemy, Alembic, Qdrant, config, logging)
- [ ] Phase 2: MCP server and client
- [ ] Phase 3: RAG pipeline
- [ ] Phase 4: Multi-agent workflow (LangGraph)
- [ ] Phase 5: Frontend and API integration
- [ ] Phase 6: Observability (OTel, metrics, Prometheus, Grafana, optional Datadog/Sentry)
- [ ] Phase 7: Testing and reliability
- [ ] Phase 8: Docker and local deployment (includes an optional `quality` Compose profile running SonarQube Community Build locally)
- [ ] Phase 9: CI/CD (GitHub Actions); static analysis with SonarQube, quality gate as a required check
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
