# Quantum Configuration Subsystem

> **Subsystem Type:** Core Foundation <br>
> **Layer:** Cross-cutting (inner Clean Architecture layer) <br>
> **Stability:** Permanent & Backward-Compatible <br>
> **Responsibility:** Environment discovery, configuration modeling, validation, and runtime consistency

---

## 1. Purpose & Scope

The **Quantum Configuration Subsystem** forms the foundation of deterministic and validated runtime configuration across the entire platform.

It governs:
- Environment variable discovery and merging.
- Strongly-typed configuration models (Pydantic-based).
- Validation by contract via reusable rules and registries.
- Thread-safe state caching and configuration snapshots.
- Unified runtime orchestration through a single access façade (`ConfigManager`).
This module is part of the `quantum.core` package,
and serves as the innermost layer in the overall Clean Architecture hierarchy.

---

## 2. Architectural Positioning

The configuration subsystem is designed as a **closed, pure, and side-effect-controlled** core component.
It exposes a single entrypoint (`ConfigManager`) and several internal layers that strictly obey _unidirectional dependency flow_:

```text
          ┌──────────────────────────────────────────────┐
          │                ConfigManager                 │
          │  (Runtime Orchestration & Access Facade)     │
          └──────────────────────────────────────────────┘
                        ▲              ▲
                        │              │
                        │              │
               ┌────────┘              └────────┐
               │                                │
     ┌──────────────────────┐        ┌─────────────────────┐
     │   Providers Layer    │        │    Runtime State    │
     │  (env_loader, etc.)  │        │    (ConfigState)    │
     └──────────────────────┘        └─────────────────────┘
               ▲                                ▲
               │                                │
               │                                │
     ┌──────────────────────┐        ┌──────────────────────┐
     │  Models Layer        │        │  Validators Layer    │
     │  (Core, Logging,     │        │  (Rules, Registry)   │
     │  MT5, Tracing)       │        └──────────────────────┘
     └──────────────────────┘
               ▲
               │
 ┌──────────────────────────────┐
 │  Contracts Layer (Protocols) │
 │  (Base + Settings Contracts) │
 └──────────────────────────────┘
```
> **Dependency flow:** `bottom → top` <br>
> **Access flow:** `top → bottom` (via ConfigManager orchestration)

---

## 3. Core Principles

| Principle                         | Description                                                                                                 |
|-----------------------------------|-------------------------------------------------------------------------------------------------------------|
| **Single Responsibility**         | Each layer defines one role only — providers load, models define, validators enforce, runtime orchestrates. |
| **Clean Architecture Compliance** | Unidirectional dependencies; `quantum.core` never imports upward.                                           |
| **Immutability & Determinism**    | Models are frozen; runtime state is controlled and atomic.                                                  |
| **Validation by Contract**        | All data entering the system passes through formally defined validation rules.                              |
| **Thread Safety**                 | Internal state mutations are guarded by re-entrant locks.                                                   |
| **Transparency & Observability**  | Every state is snapshot-able and introspectable.                                                            |
| **Long-Term Evolvability**        | Extra fields ignored, strong typing enforced, backwards-compatible schema evolution.                        |

---

## 4. Subsystem Structure

The internal directory layout of the configuration subsystem follows a strict layered and modular organization:

```text
src/quantum/core/
├── config/
│   ├── contracts/
│   │   ├── __init__.py
│   │   ├── base_contracts.py
│   │   └── settings_contracts.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── core.py
│   │   ├── logging.py
│   │   ├── mt5.py
│   │   └── tracing.py
│   ├── providers/
│   │   ├── __init__.py
│   │   └── env_loader.py
│   ├── runtime/
│   │   ├── __init__.py
│   │   ├── manager.py
│   │   └── state.py
│   ├── validators/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── registry.py
│   │   └── rules.py
│   └── __init__.py
└── __init__.py
```

### Layer-to-directory mapping:

| Layer          | Directory     | Key Components                                  | Responsibility                                                                          |
|----------------|---------------|-------------------------------------------------|-----------------------------------------------------------------------------------------|
| **Contracts**  | `contracts/`  | `base_contracts.py`, `settings_contracts.py`    | Define all configuration protocols and invariants.                                      |
| **Validators** | `validators/` | `base.py`, `rules.py`, `registry.py`            | Define reusable validation rules and the central registry.                              |
| **Models**     | `models/`     | `core.py`, `logging.py`, `tracing.py`, `mt5.py` | Define immutable, validated Pydantic models for all configuration types.                |
| **Providers**  | `providers/`  | `env_loader.py`                                 | Load and merge environment variables from layered sources (`.env`, local, process).     |
| **Runtime**    | `runtime/`    | `state.py`, `manager.py`                        | Maintain atomic configuration state and provide unified access through `ConfigManager`. |

---

## 5. Configuration Lifecycle

The configuration lifecycle follows a deterministic sequence of atomic operations:

```text
.env/.env.<env>/.env.local
          │
          ▼
[ Providers ]
  └── env_loader.load_env()
          │  merges layered environment sources
          ▼
[ Validators ]
  └── ValidatorRegistry.validate()
          │  normalizes and validates field values
          ▼
[ Models ]
  └── Pydantic models instantiated (Core, Logging, Tracing, MT5)
          │
          ▼
[ Runtime State ]
  └── ConfigState caches merged environment and snapshot
          │
          ▼
[ ConfigManager ]
  └── Exposes validated configuration to the entire platform

```

---

## 6. Interaction with Other Subsystems

| Subsystem                   | Interaction Type       | Direction    | Description                                                                         |
|-----------------------------|------------------------|--------------|-------------------------------------------------------------------------------------|
| **Observability**           | Snapshot exposure      | Outbound     | Provides non-sensitive configuration metadata for logs and metrics.                 |
| **Execution Engine**        | Read-only dependency   | Outbound     | Reads configuration via `ConfigManager.load()` APIs.                                |
| **CLI & Streamlit Apps**    | Runtime initialization | Outbound     | Bootstrap configuration at startup for consistency.                                 |
| **No inbound dependencies** | ❌                      | ⬆️ forbidden | No external subsystem imports `quantum.core.config` directly except through façade. |

> All interactions are read-only and thread-safe.

---

## 7. Extension Guidelines

When extending the configuration system, respect the invariants below:

| Category                             | Rule                                                                                                                                                   |
|--------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Adding a new configuration model** | Derive from `BaseModel` or `BaseSettings`. Keep it frozen (`ConfigDict(frozen=True)`), validated by explicit rules, and registered in `ConfigManager`. |
| **Adding a new validator**           | Implement `ValidationRule`, register in `ValidatorRegistry` with a unique `rule_id`. Write unit + integration tests.                                   |
| **Adding a new provider**            | Implement `EnvProviderProtocol` if needed (for secret manager, cloud API, etc.). Must be pure, testable, and deterministic.                            |
| **Modifying contracts**              | Requires ADR approval (see Governance Policy in `.importlinter` header).                                                                               |
| **Cross-layer imports**              | Prohibited unless explicitly whitelisted through contracts.                                                                                            |


---

## 8. Observability & Diagnostics

The configuration subsystem exposes diagnostics utilities to ensure transparency:

| Function                       | Description                                                         |
|--------------------------------|---------------------------------------------------------------------|
| `ConfigState.describe()`       | Returns a concise summary (`base_dir`, PID, number of env vars).    |
| `ConfigManager.snapshot()`     | Produces an immutable summary for metrics/logs.                     |
| `ConfigManager.clear_caches()` | Resets all caches and state — used in testing or re-initialization. |
| `get_registered_rules()`       | Returns all active validation rules and descriptions.               |

> These utilities support integration with observability pipelines (`logging`, `tracing`, `metrics`).

---

### © Quantum Platform — Configuration Subsystem

Maintained under long-term stability contract (LTS, 10+ years).
