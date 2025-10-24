# Quantum Observability

> Scope: local-first, modular observability for a professional algorithmic-trading lab.
Pillars covered: Logging, Metrics, Tracing, Bootstrap, CLI/Streamlit integrations, Governance & Security.
Codebase paths referenced are those in this repository.

---

## 1) Architecture at a glance
```text
src/quantum/infrastructure/observability/
├── logging/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── factory.py
│   │   └── log_payload_v1.py
│   ├── __init__.py
│   ├── _io_utils.py
│   ├── audit_sink.py
│   ├── constants.py
│   ├── event_emitter.py
│   ├── filters.py
│   ├── formatter.py
│   ├── logs.py
│   └── partitioned_handlers.py
├── metrics/            # Prometheus client metrics
│   ├── __init__.py
│   ├── health.py
│   └── mt5.py
├── tracing/            # OpenTelemetry setup, context propagation
│   ├── __init__.py
│   ├── propagation.py
│   └── traces.py
├── __init__.py
└── init_observability.py
```
### Key design goals
- Clean Architecture alignment: infrastructure is isolated; CLI/Streamlit integrate via bootstrap only.
- Local-first: zero hard dependency on external services. Optional OTLP exporter & /metrics http server.
- Durability & safety: atomic audit writes, opt-in fsync, quarantine of malformed lines, no-throw handlers.
- Signal quality: strict JSON schema, OTel-compatible severities, redaction, bounded labels & buckets.
- Operability: health gauges, smoke test, Streamlit observability page.

---

## 2) Environment & configuration conventions
Environment variables are loaded by `load_env(..)` with priority:

base `.env` < `.env.$QUANTUM_ENV` < `.env.local` < `OS env`.

### Identity
- `QUANTUM_APP_NAME` (e.g., `python_core`, `streamlit_ui`)
- `QUANTUM_APP_VERSION` (semver+build)
- `QUANTUM_ENV` (`dev`/`test`/`prod`)
- `QUANTUM_NS` (namespace, e.g., quantum)
- `QUANTUM_SERVICE_INSTANCE_ID` (stable node id; default=hostname)

### Logging
- `QUANTUM_LOG_LEVEL` (`DEBUG`|`INFO`|...)
- `QUANTUM_LOG_DIR` → enable partitioned JSONL to disk
- `QUANTUM_AUDIT_DIR` → enable one-file-per-event audit
- `QUANTUM_AUDIT_EVENTS` CSV allowlist (ex: `order_submit_v1`,`order_fill_v1`)
- `QUANTUM_AUDIT_EVENTS_VERSION` (`v1`), version agnostic matching
- `QUANTUM_LOG_FSYNC` (`true`|`false`) per-write fsync (POSIX)
- `QUANTUM_LOG_MAX_BYTES` (e.g., `10485760`)
- `QUANTUM_LOG_WARN_BYTES` (stderr pre-threshold hint)
- Controls: `QUANTUM_LOG_RATELIMIT`, `QUANTUM_LOG_RPS`, `QUANTUM_LOG_SAMPLE_INFO`

### Metrics
- `QUANTUM_METRICS_PORT` (`9464` to expose `/metrics`, `0` disables)
- `QUANTUM_METRICS_ADDR` (`127.0.0.1` by default)

### Streamlit (UI log tail)
- `STREAMLIT_LOG_TZ` (`utc`|`local`)
- `STREAMLIT_LOG_RENDERER` (`json`|`code`)
- `STREAMLIT_LOG_EXPANDED` (`true`|`false`)
- `STREAMLIT_LOG_CHUNK_BYTES` (e.g., `256000`)
- `STREAMLIT_LOG_TAIL_MAX_LINES` (e.g., `100`)
- `STREAMLIT_LOG_GLOB` (default `events-*.jsonl`)

---

## 3) Logging
### 3.1 JSON schema & invariants
**Model**: `LogPayloadV1` (`log_payload_v1.py`) — immutable Pydantic model.
- `timestamp`: RFC3339 UTC with millisecond precision (e.g., `2025-01-02T03:04:05.123Z`)
- `ts_unix_ms`, `ts_monotonic_ms`: optional, for latency/ordering
- Severity: `level` ∈ {TRACE, DEBUG, INFO, WARN, ERROR, FATAL}, `severity_number` ∈ [1..24] (OTel bands)
- Source: `logger`, `message`
- Resource: `env`, `instance`, `service_name`, `service_version`, `service_namespace`
- Correlation: `trace_id` (32 hex), `span_id` (16 hex), `sampled`, `correlation_id` (UUID), `run_id` (UUID)
- Exceptions: `exception_type`, `exception_message`, `exception_stacktrace` (+ legacy exception string)
- Schema tags: `schema="quantum.log"`, `log_schema_version="v1"`
- `attrs`: small, flat map for additional attributes (bounded; see policy)

**Severity mapping** (Python → OTel band) lives in `models/factory.py`:
- `NOTSET→TRACE(1)`, `DEBUG→DEBUG(5)`, `INFO→INFO(9)`, `WARNING→WARN(13)`, `ERROR→ERROR(17`), `CRITICAL→FATAL(21)`

> ##### Contract
> Timestamps and severity are normalized by the formatter + factory.
> The formatter automatically structures exception fields from `exc_info`.

### 3.2 Enrichment & formatter
`JsonFormatter`:
- Extracts current OTel context (`trace_id`, `span_id`, `sampled`) robustly across SDK versions.
- Injects timestamps from `record.created` + monotonic ms.
- Collects non-standard record fields into `attrs`, recursively sanitized (strings truncated to 10k chars, bytes compacted).
- Structured exceptions when `exc_info` is present.
- On Pydantic `ValidationError`, emits safe fallback JSON and increments `quantum_logging_schema_validation_errors_total`.

### 3.3 Filters & policies
`filters.py`:
- IgnoreLibrariesFilter: drops noisy third-party loggers.
- LoggingContextFilter: injects env early.
- MonotonicTimestampFilter: early monotonic ms.
- RedactFilter:
  - Key-based redact: `password`|`secret`|`token`|`api_key`|... → `[REDACTED]`
  - Heuristics: JWT-like tokens and 32-hex sequences → `[REDACTED]`
  - Length cap (5k chars) on strings.
  - Increments `quantum_logging_redactions_total`.
- InfoSamplerFilter: keep 1 of N INFO logs (configurable).
- RateLimitFilter: token-bucket across all severities.
- StaticFieldsFilter: injects `service_name`|`namespace`|`version`.

#### Expected filter order (authoritative)
`IgnoreLibraries → Redact → StaticFields → LoggingContext → MonotonicTimestamp → Formatter`

> ##### Policy
> - Redaction before formatting protects sinks.
> - Sampling and rate-limit may drop logs; see § Metrics (drops).
> - Keep `attrs` small and flat (≤ ~50 keys, ≤ ~8–16KiB total after JSON).

### 3.4 Sinks & durability

- Partitioned JSONL (`PartitionedJSONLFileHandler`)
- Path: `<base>/<env>/<ns>/<app>/YYYY/MM/DD/HH/events-YYYYMMDD-HH(.partN).jsonl`
- Best-effort size rollover (`QUANTUM_LOG_MAX_BYTES`), stderr “nearing threshold” hint (`QUANTUM_LOG_WARN_BYTES`).
- Quarantines malformed lines to `bad-logs-YYYYMMDD-HH(.partN).jsonl`.
- Optional per-write `fsync` (POSIX), directory fsync after open.

#### Audit files (AuditEventFileHandler)
- Single JSON per allowlisted trading event (e.g., `order_submit_v1`).
- Path: `<base>/<env>/<ns>/<app>/YYYY/MM/DD/HHMMSS-UUID.json`
- Atomic write: `tmp → fsync(file) → atomic rename → fsync(dir)`.
- Inputs come from `emit_event(..)` (Pydantic/dict), with implicit `run_id`/`correlation_id`.
- Allowlist is version-agnostic: `_v\d+` suffix ignored.

> ##### Note
> Partition and audit sinks are optional. Console JSON is always available.
> `logging_sink_up=0` simply means “no persistent writable sink”, not an error.

---

## 4) Metrics (Prometheus)
### 4.1 Health & pipeline (`metrics/health.py`)
- `quantum_build{service_name,service_version,service_namespace,env} 1` (Info metric)
- Gauges (0/1):
  - `quantum_pipeline_up` — logging and tracing initialized
  - `quantum_pipeline_logging_ok`
  - `quantum_pipeline_tracing_ok`
  - `quantum_pipeline_metrics_http_ok` — `/metrics` http server running
  - `quantum_tracing_up` (alias: otel_tracing_up)
  - `quantum_tracer_exporter_active` (OTLP attached)
  - `quantum_logging_sink_up` — at least one persistent sink is writable
- Counters:
  - `quantum_logging_file_rotations_total`
  - `quantum_logging_redactions_total`
  - `quantum_logging_schema_validation_errors_total`
  - `quantum_logging_disk_errors_total`

#### Recommended (future, documented here for governance):
  - `quantum_logs_rate_limited_total`, `quantum_logs_sampled_info_total`
  - `quantum_bad_log_lines_total`
  - Tracing exporter: `quantum_trace_export_success_total`, `quantum_trace_export_fail_total`, `quantum_trace_exporter_queue_depth`

### 4.2 MT5 metrics (metrics/mt5.py)
- Histograms (seconds): `quantum_mt5_order_check_latency_seconds`, `order_send_latency_seconds`, `intent_to_ack_seconds`, `time_to_fill_seconds`
- Counters: `quantum_mt5_requotes_total{symbol}`, `order_reject_class_total{symbol,error_class}`, optional `order_reject_total{error_code}` (guarded by `QUANTUM_MT5_ENABLE_ERROR_CODE_METRIC` + allowlist), `deals_total`, `intents_total`, `orders_total{type}`
- Gauges: `quantum_mt5_terminal_up`, `connection_status`, `positions_open`, `account_free_margin`
- Histogram: `quantum_mt5_slippage_points`, `tick_staleness_seconds`

> #### Label policy
> Keep `symbol` usage bounded (top-N only), or aggregate to `symbol="ALL"` for background flows.

### 4.3 UI metrics (`apps/streamlit/lib/obs.py`)
Histograms:
`quantum_ui_action_latency_seconds{action}`
`quantum_ui_page_render_seconds`
Counter: `quantum_ui_actions_total{action}`
Exemplars: histograms attach `{trace_id, span_id}` when supported.

---

## 5) Tracing (OpenTelemetry)
### 5.1 Provider & resources (`tracing/traces.py`)
- `TracerProvider` with `Resource` keys:
- `service.name`, `service.namespace`, `service.version`, `deployment.environment`, `service.instance.id`
- Sampling: `ParentBased(TraceIdRatioBased(QUANTUM_TRACE_SAMPLE))`
- Span limits: `max_attributes=128`, `max_events=128`, `max_links=32`
- Exporters:
  - `console` (BatchSpanProcessor)
  - `otlp` (`http` or `grpc`; lazy-import guarded)
  - `none` (no export, sampler may be 0 in fallback)

#### Security
  For remote collectors: `QUANTUM_TRACE_OTLP_INSECURE=false` (gRPC), TLS enabled. Header values must never be logged (we log only header keys).

### 5.2 Context & propagation (`tracing/propagation.py`)
- Global propagators: W3C tracecontext + baggage (`setup_propagation()`).
- Process-wide baggage: one-shot installation of `{run_id, correlation_id}`; detachable/refreshable.
- Cross-thread helpers: `ContextSnapshot`, `use_context_snapshot`, `ContextPropagatingThread`, `submit_with_context()` (Executor).
- Localized baggage injection: `baggage_context_from_ids()`.
> Multiprocessing is not auto-propagated; re-bootstrap per child or pass context explicitly.

### 5.3 Span enrichment
`_ContextEnricherProcessor` adds:
- `quantum.run_id`, `quantum.correlation_id` attributes on span start.

---

## 6) Bootstrap & lifecycle
### 6.1 Initialization (init_observability.init_observability)
Order of operations:
1. Reset health gauges (0)
2. `load_env()`; refresh `quantum_build` Info
3. Ensure `run_id` exists
4. Logging: `init_logging(..)`
5. Probe persistent sinks → `quantum_logging_sink_up`
6. Tracing: `init_tracing(..)`; `setup_propagation()`; install process baggage
   - On failure: fallback to `exporter="none"`, `sample_ratio=0.0`
7. Optionally start /metrics HTTP server (bind `QUANTUM_METRICS_ADDR:PORT`)
8. Set pillar gauges and `quantum_pipeline_up`

Idempotent & thread-safe (`_init_lock`). `force=True` cleans existing root handlers and re-inits.

### 6.2 Shutdown (`shutdown_observability`)
- Detaches process baggage, shuts down `TracerProvider` (best effort)
- Closes & removes all logging handlers from root
- Optionally resets gauges to 0 (testing)
- Leaves the Prometheus HTTP server running (library limitation)

### 6.3 Health gauges semantics
| Gauge                              | Meaning                                                            |
| ---------------------------------- | ------------------------------------------------------------------ |
| `quantum_pipeline_up`              | Both logging **and** tracing initialized successfully at last init |
| `quantum_pipeline_logging_ok`      | Logging initialization executed without exception                  |
| `quantum_pipeline_tracing_ok`      | Tracing provider created (exporter may be inactive)                |
| `quantum_logging_sink_up`          | **At least one** persistent sink is attached **and** writable      |
| `quantum_tracer_exporter_active`   | An OTLP exporter was successfully built/attached                   |
| `quantum_pipeline_metrics_http_ok` | `/metrics` HTTP server is running (optional)                       |

> Console-only mode is healthy even if `logging_sink_up=0`.

---

## 7) Interfaces & usage
### 7.1 CLI
`apps/cli/bootstrap.py`:
```python
from quantum.infrastructure.observability.bootstrap.init_manager import init_observability

def init_cli() -> None:
    init_observability()
```

`apps/cli/main.py` (simplified):
```python
from quantum.infrastructure.observability.bootstrap.init_manager import init_observability

def init_cli() -> None:
    init_observability()
```

Run:
```powershell
poetry run python -m apps.cli.main
```

### 7.2 Streamlit
`apps/streamlit/bootstrap.py`:
```python
import os

from quantum.infrastructure.observability.bootstrap.init_manager import init_observability

def init_streamlit() -> None:
    init_observability()
```

`apps/streamlit/app.py:`
```python
import streamlit as st

from apps.streamlit.bootstrap import init_streamlit
from apps.streamlit.lib.obs import PageTimer, ui_action
from quantum.core.config.runtime.manager import ConfigManager

ConfigManager.load()
st.set_page_config()
init_streamlit()

with PageTimer():  # page-level tracing + latency metric + structured log
    st.title("Desk Quant - Supervision")
    st.caption(f"run_id: {...} • corr_id: {...}")
    @ui_action("refresh_market")
    def on_refresh(): ...
```

Start Streamlit:
```powershell
make ui
```

The Observability page (`apps/streamlit/pages/observability.py`) shows KPIs, MT5 snapshot, histogram quantiles, JSONL tail, and buttons to exercise events/spans/rollover.

---

## 8) End-to-end smoke (local)

Script: `scripts/obs_smoke.py`

What it validates:
- Bootstrap (gauges up), redaction counter > 0
- Severity mapping & `severity_number` bounds
- Rollover creates `.part1.jsonl`
- Trace/log correlation inside a span
- Audit file creation with allowlisted event
- Optional `/metrics` http probe
- `tracer_exporter_active` logic (0 for console/none; 1 for otlp if exporter is built)

Basic (console exporter):
```powershell
make obs-smoke
```

With local Prometheus endpoint (/metrics):
```powershell
make obs-smoke-http
```

With OTLP/HTTP (local collector):
```powershell
make obs-smoke-otlp-http
```

With OTLP/gRPC (dev mode, insecure):
```powershell
make obs-smoke-otlp-grpc
```

Durability test (forced fsync):
```powershell
make obs-smoke-fsync
```

---

## 9) Governance: quality, security, compliance
### 9.1 Code quality & architecture
- Clean Architecture enforced by Import Linter (`.importlinter`):
  - No upward dependencies (domain ← application ← infrastructure ← interface)
  - `quantum.interface` must not import `infrastructure` or `domain`
  - `quantum.application` must not import `infrastructure`
  - `quantum.domain` must not depend on outer layers

### 9.2 Logging governance
- PII/Secrets: Redaction filter scrubs common secrets and high-entropy tokens; never put secrets into labels or long-lived storage.
- Schema stability: `quantum.log` v1 is the house schema; version field present.
- Size budgets: messages/attrs are truncated; keep attrs small & flat (≤ ~50 keys, ≤ ~8–16KiB).
- Audit policy: allowlist is version-agnostic; use snake_case names; keep allowlist tight.

### 9.3 Metrics governance
- Labels: bounded sets only (`action`, `error_class`, curated `symbol`); avoid `run_id`, `correlation_id`, order IDs, etc.
- Buckets: consistent S-curve buckets; consider adding (12.8, 25.6)s to all latency histograms if you expect long tails.
- Exposure: `/metrics` binds to loopback by default; production exposure must be explicitly configured and firewalled.

### 9.4 Tracing governance
- Security: For any remote OTLP collector, use TLS (`insecure=false`), validate certs, and never log header values.
- Propagation: threads/executors use the explicit helpers; processes re-bootstrap.

### 9.5 Continuous improvement (tracked items)
- Add counters for rate-limited and sampled logs, and bad log lines.
- Add tracing exporter success/failure counters and (if feasible) queue depth gauge.
- Document optional symbol allowlist for per-symbol metrics in env.
- Streamlit tail: optional level/logger filter.

---

## 10) Operational playbook
### 10.1 Common run modes
- Console-only (default): JSON to stderr; `logging_sink_up=0` (expected).
- File logging enabled: set `QUANTUM_LOG_DIR` and optionally `QUANTUM_LOG_FSYNC=true` (with performance cost).
- Audit enabled: set `QUANTUM_AUDIT_DIR` and `QUANTUM_AUDIT_EVENTS` CSV.
- Metrics HTTP: set `QUANTUM_METRICS_PORT=9464` (bind address via `QUANTUM_METRICS_ADDR`).
- Tracing to OTLP: set `QUANTUM_TRACE_EXPORTER=otlp`, protocol/endpoint/headers; dev gRPC may use `INSECURE=true`, production must not.

### 10.2 What to look at first when things go wrong
- Gauges on Streamlit Observability or `/metrics`:
  - `quantum_pipeline_up` (0 → check logs during init)
  - `quantum_tracer_exporter_active` (0 with `otlp` → exporter not built or misconfigured)
  - `quantum_logging_sink_up` (0 with `QUANTUM_LOG_DIR`/`_AUDIT_DIR` set → check permissions, deep probe)
- Counters:
  - `logging_schema_validation_errors_total` rising → inspect `bad-logs-*` quarantine
  - `logging_redactions_total` rising unusually → check inputs for unexpected tokens
  - `logging_file_rotations_total` increasing too fast → increase `QUANTUM_LOG_MAX_BYTES`
- Audit: presence of per-event files; if absent, confirm allowlist and `quantum.trading` logger usage.

---

## 11) Examples
### 11.1 Emit a structured event (audit-eligible)
```python
from quantum.infrastructure.observability.logging.event_emitter import emit_event

emit_event({
    "event_name": "order_submit_v1",   # must be allowlisted
    "event_version": "v1",
    "order_id": "abc-123",
    "symbol": "EURUSD",
    "side": "buy",
    "qty": 1.0,
    "price": 1.23456,
    "ts": 1720000000000,
})
```

### 11.2 Emit a log with attributes and exception
```python
import logging
log = logging.getLogger("quantum.example")

try:
    1/0
except ZeroDivisionError:
    log.error("failed compute", extra={"attrs": {"calc": "pnl"}}, exc_info=True)
```

### 11.3 UI action instrumentation
```python
from apps.streamlit.lib.obs import ui_action

@ui_action("refresh_market")
def on_refresh():
    ...
```

---

## 12) Glossary
- Audit event: singular JSON artifact for critical trading actions (e.g., `order_submit_v1`).
- Allowlist: version-agnostic set of allowed bare event names ("`_v\d+`" suffix ignored).
- Process baggage: global key-value (`run_id`, `correlation_id`) attached once to the OTel context.
- Partitioned JSONL: hourly, size-rotated log files in an S3-like directory hierarchy.

---

This observability stack is production-ready for a local-first quant lab with a clear path to distributed/exporting setups.
The contracts above (filter order, schema invariants, label budgets, security posture) are the source of truth.
When extending, keep changes schema-versioned, labels bounded, and never let observability break the trading loop.
