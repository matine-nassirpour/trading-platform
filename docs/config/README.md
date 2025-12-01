# Quantum Configuration Subsystem
> The Quantum Configuration Subsystem provides a fully deterministic, safety-grade, multi-layer configuration pipeline
> designed for long-term maintainability, reproducibility, and auditability.
>
> It separates pure and impure logic with strict boundaries, uses a formal finite state machine (FSM) as its backbone,
> ensures reproducible READY states via canonical hashing, and exposes a stable public API through the `ConfigManager` façade.

---

## 1. Design Goals
- Deterministic behavior under all runtime conditions
- Strict purity boundaries (pure core, impure shell)
- Safety-critical compatibility (DO-178C, IEC 62304, NASA SAS)
- Reproducible configuration snapshots via canonical JSON + SHA-256
- Single authoritative READY state per process
- Immutable environment snapshots
- Strict validation with early failure
- Absolute testability and isolation of side effects
- Designed for long-term evolution without breaking semantics

---

## 2. Configuration Lifecycle Overview
The configuration lifecycle follows a strictly monotonic state machine:

```markdown
UNINITIALIZED
    ↓
ENV_PATH_RESOLVED
    ↓
ENV_LOADED
    ↓
MODEL_BUILT
    ↓
MODEL_VALIDATED
    ↓
MODEL_FROZEN
    ↓
READY
```
Any violation of invariants immediately triggers a fail-fast `ERROR` state.

---

## 3. Configuration State Machine (FSM)

The FSM enforces:
- Legal transitions only
- Immutable snapshots
- Deterministic state evolution
- Strict invariants for each phase
- No I/O and no side effects

It guarantees that the configuration reaches a READY state only if:
- environment resolution succeeded
- environment loading succeeded
- model construction succeeded
- model validation succeeded
- the final model is frozen and immutable

---

## 4. Overall Architectural Diagram

```
                  ┌───────────────────────────────────┐
                  │           External World          │
                  │    (.env files, OS env vars)      │
                  └───────────────────────────────────┘
                                    │
                                    │  I/O (impure)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     CONFIGURATION LOADING PIPELINE                     │
└────────────────────────────────────────────────────────────────────────┘

STEP 1 — ENV PATH RESOLUTION (impure)
┌────────────────────────────────────────────────────────────────────────┐
│ resolve_env(root, env_file)                                            │
│  • Production rules                                                    │
│  • Explicit .env overrides                                             │
│  • Implicit discovery in non-prod                                      │
│                                                                        │
│ OUTPUT → EnvResolutionResult(base_dir, env_file?)                      │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                              Pure FSM step
                     (UNINITIALIZED → ENV_PATH_RESOLVED)

STEP 2 — ENV LOADING (impure I/O + caching)
┌────────────────────────────────────────────────────────────────────────┐
│ load_env_from_resolved(resolution):                                    │
│   • _load_env_files(base_dir, env_file?)  ← actual disk reads          │
│       - layered: .env, .env.<env>, .env.local (non-prod)               │
│   • get_frozen_env() ← immutable OS env snapshot                       │
│   • Merge: OS env < overridden by < .env files                         │
│   • Cache in ProcessLocalState (thread-safe, fork-safe)                │
│                                                                        │
│ OUTPUT → effective_env : dict[str,str]                                 │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                              Pure FSM step
                               (ENV_LOADED)

STEP 3 — BUILD MODELS (impure: Pydantic)
┌────────────────────────────────────────────────────────────────────────┐
│ validate_environment_keys_strict(models, env)                          │
│   • reject case-violations                                             │
│   • ignore unknown variables                                           │
│                                                                        │
│ EnvironmentModelRouter.route(models, env):                             │
│   → core_env, logging_env, tracing_env, mt5_env                        │
│                                                                        │
│ Instantiate Pydantic models:                                           │
│   • CoreSettings(**core_env)                                           │
│   • LoggingSettings(**logging_env)                                     │
│   • TracingSettings(**tracing_env)                                     │
│   • MT5Settings(**mt5_env)                                             │
│                                                                        │
│ OUTPUT → settings_dict = { core, logging, tracing, mt5 }               │
│          metadata = {orphans?}                                         │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                              Pure FSM step
                              (MODEL_BUILT)

STEP 4 — VALIDATE MODELS (pure)
┌────────────────────────────────────────────────────────────────────────┐
│ Pure FSM transition → MODEL_VALIDATED                                  │
│ (Pydantic validators already applied)                                  │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼

STEP 5 — FREEZE MODELS (pure)
┌────────────────────────────────────────────────────────────────────────────┐
│ Pure FSM transition → MODEL_FROZEN                                         │
│   • settings dict now treated as frozen                                    │
└────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼

STEP 6 — READY (pure)
┌────────────────────────────────────────────────────────────────────────────┐
│ Pure FSM transition → READY                                                │
│ READY state contains:                                                      │
│   • env (effective_env)                                                    │
│   • settings (frozen dict of 4 groups)                                     │
│   • metadata                                                               │
└────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼

READY STATE CACHE (pure + thread-safe)
┌────────────────────────────────────────────────────────────────────────────┐
│ ReadyStateCache                                                            │
│   • Serialize READY state in canonical JSON                                │
│   • Compute fingerprint: SHA256-V1:<digest>                                │
│   • Cache only if fingerprint changes                                      │
│                                                                            │
│ Provides: READY singleton for the entire process                           │
└────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼

CONFIG MANAGER (public façade)
┌────────────────────────────────────────────────────────────────────────────┐
│ ConfigManager._get_ready_state():                                          │
│   • Returns cached READY state OR                                          │
│   • Triggers full FSM lifecycle once                                       │
│                                                                            │
│ load_core_cached()    → CoreSettings                                       │
│ load_logging_cached() → LoggingSettings                                    │
│ load_tracing_cached() → TracingSettings                                    │
│ load_mt5_cached()     → MT5Settings                                        │
│                                                                            │
│ Also provides non-cached constructors      → CoreSettings(**env)           │
└────────────────────────────────────────────────────────────────────────────┘


USER-LAND
┌────────────────────────────────────────────────────────────────────────────┐
│ app.py                                                                     │
│                                                                            │
│ core     = ConfigManager.load_core_cached()                                │
│ logging  = ConfigManager.load_logging_cached()                             │
│ tracing  = ConfigManager.load_tracing_cached()                             │
│ mt5      = ConfigManager.load_mt5_cached()                                 │
│                                                                            │
│ → Settings fully validated, deterministic, safe, frozen                    │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Boundary Diagram (Pure vs Impure)
```
┌──────────────────────────┐
│     IMPURE (I/O)         │
│                          │
│  resolve_env()           │
│  load_env_from_resolved()│
│  Pydantic model parsing  │
└───────────┬──────────────┘
            │
            ▼
┌──────────────────────────┐
│  PURE (deterministic)    │
│                          │
│  FSM Pipeline            │
│  FSM Controller          │
│  FSM States (immutable)  │
│  ReadyStateCache         │
│  Validators              │
│  ModelRouter             │
│  Sensitive masking       │
└───────────┬──────────────┘
            │
            ▼
┌──────────────────────────┐
│  PUBLIC API (Facade)     │
│  ConfigManager           │
└──────────────────────────┘
```

---

## 6. Data Schema (structure flow)
```
OS + .env Files
      │
      ▼
EnvResolutionResult
      │
      ▼
effective_env: dict[str,str]
      │
      ▼
Routing per model
(core_env, logging_env, tracing_env, mt5_env)
      │
      ▼
Pydantic Models (4 groups)
      │
      ▼
settings_dict
      │
      ▼
FSM States (immutable)
UNINITIALIZED → ... → READY
      │
      ▼
ReadyStateCache (fingerprint)
      │
      ▼
USER SETTINGS (CoreSettings, LoggingSettings, ...)
```
