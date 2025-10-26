# Quantum Observability Stack

> **Scope:** local-first, modular observability for a professional algorithmic-trading lab. <br>
> **Pillars covered:** Logging · Metrics · Tracing · Bootstrap · CLI/Streamlit integrations · Governance & Security. <br>
> All code paths referenced are within this repository.

The **Quantum Observability Subsystem** provides the foundational telemetry infrastructure for the Quantum Platform.
It delivers unified, context-aware observability across all services and execution contexts — from automated trading back-ends to Streamlit supervision interfaces.

---

## Design Philosophy

- **Clean Architecture:** strict separation of concerns and directionally safe dependencies.
- **SOLID / DRY:** single-responsibility modules, immutable state, explicit contracts.
- **Determinism:** no global mutable state outside managed contextvars.
- **Observability Reflexivity:** the stack *observes itself* via diagnostics and metrics.
- **Longevity:** designed for maintainability and extensibility over a 10-year horizon.

---

## Architecture at a glance
```text
src/quantum/infrastructure/observability/
├── observability/
│   ├── bootstrap/
│   │   ├── __init__.py
│   │   ├── diagnostics.py
│   │   ├── health_registry.py
│   │   ├── init_manager.py
│   │   ├── lifecycle.py
│   │   └── state.py
│   ├── logging/
│   │   ├── filters/
│   │   │   ├── __init__.py
│   │   │   ├── audit_event_filter.py
│   │   │   ├── context_filter.py
│   │   │   ├── ignore_libraries_filter.py
│   │   │   ├── info_sampler_filter.py
│   │   │   ├── monotonic_timestamp_filter.py
│   │   │   ├── rate_limit_filter.py
│   │   │   ├── redact_filter.py
│   │   │   └── static_fields_filter.py
│   │   ├── formatters/
│   │   │   ├── __init__.py
│   │   │   └── json_formatter.py
│   │   ├── handlers/
│   │   │   ├── __init__.py
│   │   │   ├── audit_sink_handler.py
│   │   │   └── partitioned_handler.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── factory.py
│   │   │   ├── log_payload_v1.py
│   │   │   └── severity_map.py
│   │   ├── __init__.py
│   │   ├── _io_utils.py
│   │   ├── constants.py
│   │   ├── event_emitter.py
│   │   └── service.py
```
| Layer         | Purpose                                                                                        | Technologies                    |
|---------------|------------------------------------------------------------------------------------------------|---------------------------------|
| **Logging**   | Structured, schema-validated JSON logging with redaction and OTel correlation.                 | Python `logging`, OpenTelemetry |
| **Metrics**   | High-granularity Prometheus metrics for health, MT5 performance, and infrastructure telemetry. | `prometheus_client`             |
| **Tracing**   | Distributed tracing with full correlation (`run_id`, `correlation_id`) and W3C propagation.    | OpenTelemetry SDK               |
| **Bootstrap** | Unified lifecycle orchestration and health governance for the entire observability stack.      | Pure Python                     |

Each layer is fully decoupled, context-safe, and independently testable, following **Clean Architecture** and **SOLID** principles.

### Layer Relationships

```text
[ Application / CLI / Streamlit ]
                │
                ▼
     [ Observability Bootstrap ]
         ├── Logging Service
         ├── Metrics Collectors
         ├── Tracing Provider
         └── Diagnostics & Health Registry
```
Each subsystem can operate autonomously (local-first design),
while the LifecycleService ensures coordinated initialization, health reporting, and graceful shutdown across all observability pillars.

---

## Runtime Composition

The **Observability stack** formalizes all telemetry initialization, supervision, and shutdown
into a deterministic and thread-safe lifecycle, coordinated by the `LifecycleService`.


### Initialization Sequence

The initialization sequence is orchestrated by
`quantum.infrastructure.observability.bootstrap.init_manager.init_observability()`
and follows a strict, idempotent order:

| Step | Subsystem                 | Responsibility                                                                                                                                         |
|------|---------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1    | **Configuration**         | Load all configuration models (`core`, `logging`, `tracing`) from `ConfigManager`.                                                                     |
| 2    | **Registry**              | Create or retrieve the singleton `HealthRegistry`, which owns all Prometheus health gauges.                                                            |
| 3    | **Diagnostics**           | Initialize reflexive metrics (`quantum_observability_init_duration_seconds`, `quantum_observability_init_failures_total`).                             |
| 4    | **Build Info**            | Refresh `quantum_build` info metric from environment (`service_name`, `version`, `namespace`, `env`).                                                  |
| 5    | **Correlation Context**   | Ensure `run_id` exists (context-scoped) before any logging or tracing operation.                                                                       |
| 6    | **Tracing Subsystem**     | Initialize tracing provider via `LifecycleService.init_tracing()`. <br>Creates `TracerProvider`, installs propagators, and sets process-level baggage. |
| 7    | **Logging Subsystem**     | Initialize structured logging (`init_logging_safe()`), including filters, formatters, and persistent sinks.                                            |
| 8    | **Sink Probing**          | Validate that at least one persistent log sink (partitioned or audit) is writable; update `logging_sink_up`.                                           |
| 9    | **Metrics HTTP Exporter** | Optionally start the Prometheus exporter (`start_http_server` on configured `addr:port`).                                                              |
| 10   | **Pipeline Health**       | Consolidate health state: set `pipeline_up=1` if logging, tracing, and metrics initialized successfully.                                               |


### Thread-Safety and Idempotency

- All entrypoints are **guarded by reentrant locks** (`_init_lock` in `init_manager`).
- Safe to call `init_observability(force=False)` multiple times — the second call will no-op.
- `force=True` clears cached configuration and reinitializes all subsystems deterministically.
- Gauges and diagnostic metrics are **consistent across reinitializations**.

### Shutdown Sequence

The shutdown flow, managed by
`quantum.infrastructure.observability.bootstrap.init_manager.shutdown_observability()`,
performs an ordered and safe teardown:

| Step | Action                       | Notes                                                              |
|------|------------------------------|--------------------------------------------------------------------|
| 1    | Detach OpenTelemetry baggage | Cleanly remove `{run_id, correlation_id}` from process context.    |
| 2    | Shutdown tracing provider    | Calls `TracerProvider.shutdown()` (best-effort).                   |
| 3    | Close all logging handlers   | Safely closes and removes all sinks from root and trading loggers. |
| 4    | Optionally reset gauges      | For testing or forced reinitialization.                            |
| 5    | Reset internal state         | `_initialized = False`; ready for next init cycle.                 |

> The Prometheus HTTP exporter (if any) remains active until process exit
> — this is an intentional limitation of the underlying `prometheus_client`.

---

## Tracing - Advanced Context Propagation Model

The **Tracing subsystem** provides full OpenTelemetry (OTel) integration with explicit and deterministic
context propagation across threads, executors, and process boundaries.
It formalizes correlation at three layers — `run_id`, `correlation_id`, and OpenTelemetry trace identifiers —
ensuring coherent linkage between all log, metric, and trace signals.

### Context Hierarchy

| Context Level           | Identifier                       | Scope          | Origin                  | Storage        | Purpose                                                  |
|-------------------------|----------------------------------|----------------|-------------------------|----------------|----------------------------------------------------------|
| **Run Context**         | `run_id`                         | Process-wide   | Quantum core bootstrap  | `contextvars`  | Identifies a single logical trading run (session-level). |
| **Correlation Context** | `correlation_id`                 | Request / Task | `correlation_context()` | `contextvars`  | Links causally related actions (per task / thread).      |
| **Trace Context**       | `trace_id`, `span_id`, `sampled` | Distributed    | OpenTelemetry SDK       | OTel `Context` | Connects distributed traces across services.             |
| **Baggage Context**     | `{run_id, correlation_id}`       | Propagated     | Process + OTel baggage  | OTel `Context` | Ensures cross-propagation of app-level identifiers.      |

All contexts are **explicitly managed** — no implicit thread inheritance or global state mutation.
This guarantees deterministic behavior under multithreading, async tasks, and concurrent futures.

---

### © Quantum Platform — Observability Subsystem

Maintained under long-term stability contract (LTS, 10+ years).
