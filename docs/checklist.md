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

## Code quality tooling: SonarQube

- **Local:** SonarQube Community Build (free, self-hosted) in a Docker Compose `quality`
  profile, started on demand. Analyzes Python and TypeScript with pytest coverage reports.
- **CI:** SonarQube Cloud free plan for this public repository is the candidate for GitHub
  Actions, because it supports pull request analysis. To be confirmed in Phase 9 against the
  plan's current limits before enabling; no paid plan will be enabled.
- **Secrets:** the Sonar token is a secret file locally and a GitHub Actions secret in CI.
- **Caveats:** the local server needs about 2 GB of RAM and, on Windows, a WSL2
  `vm.max_map_count` setting for its embedded search engine. The Community Build analyzes
  only the main branch, not pull requests.
- **Scope:** configuration (`sonar-project.properties`) and the quality gate arrive in Phases 8
  and 9. Ruff and pytest remain the primary checks; Sonar adds analysis and coverage tracking.

