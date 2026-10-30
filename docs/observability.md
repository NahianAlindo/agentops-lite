# Observability plan

OpenTelemetry is the single instrumentation layer. The app sends OTLP to an **OpenTelemetry
Collector**, which routes telemetry to one or both backends. The app does not know which backend
is in use. It must run with every exporter disabled (`OTEL_ENABLED=false`) and when any backend
is unreachable.

## Two routes

| Route | Backends | Purpose | Cost |
|---|---|---|---|
| **Local** | Prometheus (metrics), Grafana Tempo (traces), Grafana (dashboards) | Offline development, and the permanent route after hosted access ends | $0, Docker containers |
| **Hosted** | Datadog (traces, metrics, logs, dashboards, monitors) | Hosted observability while the student offer is active | Student offer only; no paid plan |

Both routes can run at once: the Collector fans out the same OTLP stream. Only one hosted platform
receives traces, metrics and logs, so nothing is duplicated across hosted services. Logs are JSON
on stdout locally (read with `docker compose logs`); Loki is not added unless a need appears.

## Signals

| Signal | Plan |
|---|---|
| Traces | FastAPI, outgoing HTTP, agent runs, MCP tool calls, embedding, Qdrant retrieval, LLM calls, all under one request trace |
| Metrics | API (count, latency, errors), agents (jobs, duration, iterations, timeouts), LLM (latency, failures, tokens), MCP, RAG, rate limiter, infra |
| Logs | Structured JSON with trace/span IDs; secrets, prompts and file contents redacted |
| Dashboards and monitors | Grafana (local) and Datadog (hosted): API health, agent performance, LLM latency, RAG retrieval, errors; Datadog monitors for failure rate and latency |
| Infrastructure (Kubernetes phase) | Local: kube-state-metrics and container metrics in Prometheus. Hosted: Datadog (Agent added only if the Collector cannot supply what is needed) |
| Errors | Sentry (optional): unhandled exceptions only, with release info and trace id; no traces or metrics sent there |

## Sequencing

- **Phase 1:** structured logging, request ids, and instrumentation seams only.
- **Phase 1b (right after Phase 1):** confirm Datadog access, limits and expiry; enable
  OpenTelemetry in the API; run the Collector with the Datadog exporter; API traces, metrics and
  correlated logs in Datadog; an API dashboard and one monitor.
- **Phases 2 and 3:** MCP and RAG spans and metrics are added as part of those phases.
- **Phase 4b (right after Phase 4):** agent and LLM telemetry; workflow dashboard; controlled
  failure demonstration; screenshots and a trace walkthrough stored in the repository docs.
- **Phase 6:** the local route (Prometheus, Tempo, Grafana and its dashboards), Sentry, redaction
  hardening, infrastructure metrics, and final documentation.

## Cost and eligibility

- Datadog is used only while the GitHub Student Developer Pack offer (or a suitable free
  allowance) is active. Verify eligibility, limits and expiry before enabling; never enable a paid
  plan. The pack runs until December 2026 (renewal not assumed): capture Datadog evidence while
  access is active. Afterwards the hosted exporter is turned off and the local route remains.
- Sentry is used only if its current free allowance meets the needs.
- API keys (`datadog_api_key`, `sentry_dsn`) are secret files, never committed.

## Rules

No user IDs, repo URLs or raw queries in metric labels (high cardinality); no prompts or source
content in telemetry by default; redaction applies to logs, traces and error events before export.
