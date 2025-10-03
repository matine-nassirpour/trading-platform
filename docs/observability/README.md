# Observability – Trading Platform

> This document describes the local observability stack integrated into the trading platform.
It explains how to validate, monitor, and explore logs, traces, metrics, and audit events.

---

## 📌 Components

- Logging
  - Structured JSON logs (partitioned, size-based rollover).
  - Redaction of sensitive fields.
  - “Bad logs” quarantine for malformed entries.
- Tracing
  - OpenTelemetry spans (console, otlp, or disabled).
  - Context propagation (correlation IDs, run IDs).
- Metrics
  - Prometheus-compatible /metrics endpoint.
  - Gauges, counters, and histograms for pipeline and UI.
- Audit Events
  - Validated JSON audit records for whitelisted business events.
- UI
  - Streamlit Observability page:
    - Emit demo logs/events.
    - Inspect recent JSON logs.
    - Monitor pipeline status.
    - Quick link to `/metrics`.



## 🚀 Quick Start
### 1. Run the Smoke Test
Validate the observability stack end-to-end:
```powershell
make obs-smoke
make obs-smoke-http
make obs-smoke-otlp-http
make obs-smoke-otlp-grpc
make obs-smoke-fsync
```

### 2. Launch Streamlit Observability UI
```powershell
make ui
```
- Open the **Observability** page.
- Emit logs, audit events, and test redaction.
- Tail the most recent `events-*.jsonl` file.
- View pipeline health.

### 3. Inspect Prometheus Metrics
Open in browser:
```
http://127.0.0.1:<port>/metrics
```

Example output:
```text
quantum_pipeline_up 1.0
quantum_pipeline_logging_ok 1.0
quantum_pipeline_tracing_ok 1.0
quantum_pipeline_metrics_http_ok 1.0
quantum_logging_redactions_total 2.0
quantum_ui_page_render_ms_count 3.0
```

### 4. Grafana Dashboard (Optional)
Import the JSON file into Grafana:
```
docs/observability/grafana_dashboard.json
```

## 📂 Log & Audit File Structure
Logs are stored in:
```
_logs/<env>/<namespace>/<app>/<year>/<month>/<day>/<hour>/
```

Audit events are stored in:
```
_audit/<env>/<namespace>/<app>/<year>/<month>/<day>/<hour>/
```
- `events-*.jsonl` → valid logs.
- `bad-logs-*.jsonl` → quarantined invalid lines.
- `audit-*.json` → validated audit records.

## ⚙️ Configuration (Env Vars)
- `QUANTUM_LOG_DIR` → base directory for logs.
- `QUANTUM_AUDIT_DIR` → base directory for audit files.
- `QUANTUM_LOG_MAX_BYTES` → file rollover threshold.
- `QUANTUM_TRACE_EXPORTER` → `console`, `otlp`, or `none`.
- `QUANTUM_METRICS_PORT` → port for `/metrics` endpoint.
See `.env.example` for the complete list.
