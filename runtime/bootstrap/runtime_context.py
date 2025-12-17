from __future__ import annotations

from dataclasses import dataclass

from runtime.bootstrap.contexts.config import RuntimeConfigContext
from runtime.bootstrap.contexts.identity import RuntimeIdentityContext
from runtime.bootstrap.contexts.observability import RuntimeObservabilityContext

from quantum.infrastructure.config.runtime.manager import ConfigManager
from quantum.infrastructure.config.runtime.state.ready_cache import ReadyStateCache
from quantum.infrastructure.config.validators.runtime import initialize_validators


@dataclass(frozen=True)
class RuntimeContext:
    """
    Aggregate runtime context.

    Responsibility:
    - Aggregate specialized runtime sub-contexts
    - Provide a clear handoff object to the assembly layer

    NO logic.
    NO lifecycle.
    """

    identity: RuntimeIdentityContext
    observability: RuntimeObservabilityContext
    config: RuntimeConfigContext


def bootstrap_runtime_context(
    *, root: str | None = None, env_file: str | None = None
) -> RuntimeContext:
    """
    Main Composition Root of the whole software system.

    Responsibilities:
        - Load environment layers (.env base, env-specific, local)
        - Instantiate validated configuration models
        - Produce a fully-configured QuantumRuntime instance
    """
    # 1. Initialize validator registry (required for Pydantic models)
    initialize_validators()

    # 2. Warm-up configuration subsystem
    state = ConfigManager.run_fsm(
        root=root,
        env_file=env_file,
    )

    # 3. Store READY state in ReadyStateCache
    ReadyStateCache.set(state)

    core = ConfigManager.load_core_cached()
    logging_settings = ConfigManager.load_logging_cached()
    tracing_settings = ConfigManager.load_tracing_cached()
    # mt5_settings = ConfigManager.load_mt5_cached()

    identity = RuntimeIdentityContext(core_settings=core)
    config = RuntimeConfigContext(core_settings=core)

    observability = RuntimeObservabilityContext(
        identity=identity,
        logging_settings=logging_settings,
        tracing_settings=tracing_settings,
        metrics_host=core.quantum_metrics_host,
        metrics_port=core.quantum_metrics_port,
    )

    return RuntimeContext(
        identity=identity,
        observability=observability,
        config=config,
    )
