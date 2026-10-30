# Implementation checklist

- [x] Phase 0: Repository setup and planning
- [ ] Phase 1: Backend and data layer (FastAPI, SQLAlchemy, Alembic, Qdrant, config, logging)
- [ ] Phase 2: MCP server and client
- [ ] Phase 3: RAG pipeline
- [ ] Phase 4: Multi-agent workflow (LangGraph)
- [ ] Phase 5: Frontend and API integration
- [ ] Phase 6: Observability (OTel, metrics, Prometheus, Grafana, optional Datadog/Sentry)
- [ ] Phase 7: Testing and reliability
- [ ] Phase 8: Docker and local deployment
- [ ] Phase 9: CI/CD (GitHub Actions)
- [ ] Phase 10: Terraform and Kubernetes (local first; AKS only with explicit approval)
- [ ] Phase 11: Public demo and documentation

## Known risks

- Python 3.14 default vs ML wheel availability (mitigated: pinned to 3.12).
- Groq free-tier rate limits: needs caching, bounded iterations, no blind retries.
- GitHub unauthenticated API rate limit (60/hr): optional read-only token, caching.
- Embedding model download size (first run); keep the model small.
- Prompt injection from repository content and docs: treat as untrusted.
