# Observability plan

OpenTelemetry is the single instrumentation layer; exporters are env-configured and optional.
The app must run with every exporter disabled (`OTEL_ENABLED=false`).

| Signal | Plan |
|---|---|
| Traces | FastAPI, outgoing HTTP, agent runs, MCP tool calls, embedding, Qdrant retrieval, LLM calls, all under one request trace |
| Metrics | API (count, latency, errors), agents (jobs, duration, iterations, timeouts), LLM (latency, failures, tokens), MCP, RAG, infra |
| Logs | Structured JSON with trace/span IDs; secrets, prompts and file contents redacted |
| Local stack | Prometheus + Grafana via a Docker Compose profile |
| Hosted | Datadog only if the student offer is eligible; Sentry only if it adds value |

Rules: no user IDs, repo URLs or raw queries in metric labels; no prompts or source content in
telemetry by default; no telemetry to multiple hosted platforms without a reason.

Implementation lands in Phases 1 (logging, instrumentation hooks), 4 (agent/LLM spans) and 6 (full setup).
