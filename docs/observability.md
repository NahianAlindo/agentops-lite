# Observability plan

OpenTelemetry is the single instrumentation layer. Telemetry leaves the app over OTLP to a
Datadog Agent; exporters are env-configured and optional. The app must run with every exporter
disabled (`OTEL_ENABLED=false`) and when Datadog or Sentry is unreachable.

| Signal | Plan |
|---|---|
| Traces | FastAPI, outgoing HTTP, agent runs, MCP tool calls, embedding, Qdrant retrieval, LLM calls, all under one request trace |
| Metrics | API (count, latency, errors), agents (jobs, duration, iterations, timeouts), LLM (latency, failures, tokens), MCP, RAG, rate limiter, infra |
| Logs | Structured JSON with trace/span IDs; secrets, prompts and file contents redacted |
| Dashboards and monitors | Datadog: API health, agent performance, LLM latency, RAG retrieval, errors; monitors for failure rate and latency |
| Infrastructure | Datadog Agent: CPU/memory, container restarts, pod readiness, HPA replica counts (Kubernetes phase) |
| Errors | Sentry (optional): unhandled exceptions only, with release info and trace id; no traces or metrics sent there |

## Division of responsibility

- **Datadog** receives traces, metrics and logs. It is the single place to follow a request.
- **Sentry** receives exceptions only, so no telemetry is duplicated across platforms. Each event
  carries the trace id, so it links back to the Datadog trace.
- **Local development** without Datadog: exporters are off, or an OpenTelemetry console exporter
  can print spans for debugging. There are no local dashboards; this is a trade-off of dropping
  Prometheus and Grafana.

## Sequencing: Datadog slice pulled forward

The Student Pack deadline (below) means Datadog work is not left to Phase 6. It is split into two
checkpoints, each delivered through the normal 0-6 stage workflow with its own PRs:

- **Phase 1b (right after Phase 1):** confirm Datadog access, plan limits and expiry; enable
  OpenTelemetry in the API; send request traces, API metrics and correlated logs through a
  Datadog Agent; build an API dashboard and one monitor. This proves ingestion early.
- **Phase 4b (right after Phase 4):** add agent, MCP, RAG and LLM spans and metrics; build the
  workflow dashboard; run a controlled failure demonstration; capture screenshots and a trace
  walkthrough into the repository docs while access is active.

Spans for MCP (Phase 2) and RAG (Phase 3) are added as part of those phases, so 4b only has to
connect and demonstrate them. Phase 6 keeps the rest: Sentry, redaction hardening, infrastructure
metrics, and final documentation.

## Cost and eligibility

- Datadog is used only if the GitHub Student Developer Pack offer (or a suitable free allowance)
  is available and activated. Eligibility, limits and expiry must be verified before enabling; a
  paid plan will not be enabled. If the offer or a trial ends, set `OTEL_ENABLED=false`; the
  application is unaffected.
- The author's GitHub Student Developer Pack runs until December 2026 (renewal not assumed).
  Datadog benefits tied to the pack may end then, so: capture Datadog evidence (dashboards,
  traces, the failure demonstration) while access is active, store it in the repository docs,
  and keep the app fully functional with Datadog disabled afterwards.
- Sentry is used only if its current free allowance meets the needs.
- API keys (`datadog_api_key`, `sentry_dsn`) are secret files, never committed.

## Rules

No user IDs, repo URLs or raw queries in metric labels (high cardinality); no prompts or source
content in telemetry by default; redaction applies to logs, traces and error events before export.

Implementation lands in Phases 1 (logging, instrumentation hooks), 4 (agent/LLM spans) and
6 (full setup).
