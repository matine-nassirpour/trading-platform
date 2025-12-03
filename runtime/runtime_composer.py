"""
Quantum Runtime Composition Root

Responsibilities
----------------
- Instantiate configuration, identity and observability subsystems.
- Assemble application ports, adapters and runtime services.
- Produce a fully-initialized QuantumRuntime object.

Notes
-----
This module is part of the external composition root.
It is allowed to import any architectural layer, because it is not
itself part of the Clean Architecture core.
"""

from __future__ import annotations

import logging

from typing import Final

from quantum.application.ports.outbound.time_provider_port import TimeProviderPort
from quantum.infrastructure.config.models.core import CoreSettings
from quantum.infrastructure.config.models.logging import LoggingSettings
from quantum.infrastructure.config.models.mt5 import MT5Settings
from quantum.infrastructure.config.models.tracing import TracingSettings
from quantum.infrastructure.config.runtime.manager import ConfigManager
from quantum.infrastructure.config.runtime.state.ready_cache import ReadyStateCache
from quantum.infrastructure.config.validators.runtime import initialize_validators
from quantum.infrastructure.observability.bootstrap.init_manager import (
    init_observability,
    shutdown_observability,
)
from quantum.infrastructure.observability.bootstrap.lifecycle.configs.logging_config import (
    LoggingConfig,
)
from quantum.infrastructure.observability.bootstrap.lifecycle.configs.metrics_config import (
    MetricsConfig,
)
from quantum.infrastructure.observability.bootstrap.lifecycle.configs.tracing_config import (
    TracingConfig,
)
from quantum.infrastructure.observability.foundation.config.identity_runtime_bundle import (
    IdentityRuntimeBundle,
)
from quantum.infrastructure.time.time_provider_adapter import SystemTimeProviderAdapter

LOGGER: Final = logging.getLogger("quantum.runtime.composer")


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Internal Helper                                                            │
# ╰────────────────────────────────────────────────────────────────────────────╯
def _parse_log_level(level: str) -> int:
    """Convert validated uppercase string (INFO, DEBUG…) to logging level int."""
    return getattr(logging, level.upper(), logging.INFO)


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Runtime Object                                                             │
# ╰────────────────────────────────────────────────────────────────────────────╯
class QuantumRuntime:
    def __init__(
        self,
        *,
        core_settings: CoreSettings,
        logging_settings: LoggingSettings,
        tracing_settings: TracingSettings,
        mt5_settings: MT5Settings,
        time_provider: TimeProviderPort,
    ) -> None:
        self._core = core_settings
        self._logging_cfg = logging_settings
        self._tracing_cfg = tracing_settings
        self._mt5_cfg = mt5_settings
        self._time_provider = time_provider

        self._observability_initialized = False

    # --------------------------------------------------------------------------
    # Adapters — convert Pydantic Settings → Observability Value Objects
    # --------------------------------------------------------------------------
    def _make_identity(self) -> IdentityRuntimeBundle:
        c = self._core
        return IdentityRuntimeBundle(
            environment=c.quantum_env,
            service_namespace=c.quantum_ns,
            service_name=c.quantum_app_name,
            service_version=c.quantum_app_version,
            instance_id=c.quantum_instance_id or "unknown",
        )

    def _make_logging_config(self) -> LoggingConfig:
        s = self._logging_cfg
        return LoggingConfig(
            identity=self._make_identity(),
            log_dir=s.quantum_log_dir.as_path(),
            audit_dir=s.quantum_audit_dir.as_path(),
            audit_allowlist=s.quantum_audit_allowlist,
            log_level=_parse_log_level(s.quantum_log_level),
            sample_info_every=s.quantum_log_sample_info,
            ratelimit_rps=float(s.quantum_log_rps),
            log_fsync=s.quantum_log_fsync,
            log_max_bytes=s.quantum_log_max_bytes,
            log_warn_bytes=s.quantum_log_warn_bytes,
        )

    def _make_tracing_config(self) -> TracingConfig:
        s = self._tracing_cfg
        return TracingConfig(
            identity=self._make_identity(),
            trace_exporter=s.quantum_trace_exporter,
            trace_otlp_endpoint=s.quantum_trace_otlp_endpoint,
            trace_otlp_protocol=s.quantum_trace_otlp_protocol,
            trace_otlp_headers=s.quantum_trace_otlp_headers or "",
            trace_otlp_timeout_ms=s.quantum_trace_otlp_timeout_ms,
            trace_otlp_compression=s.quantum_trace_otlp_compression,
            trace_otlp_insecure=s.quantum_trace_otlp_insecure,
            trace_sample=s.quantum_trace_sample,
        )

    def _make_metrics_config(self) -> MetricsConfig:
        c = self._core
        return MetricsConfig(
            host=c.quantum_metrics_host,
            port=c.quantum_metrics_port,
        )

    # --------------------------------------------------------------------------
    # Observability lifecycle
    # --------------------------------------------------------------------------
    def initialize_observability(self) -> bool:
        if self._observability_initialized:
            return True

        try:
            ok = init_observability(
                logging_config=self._make_logging_config(),
                tracing_config=self._make_tracing_config(),
                metrics_config=self._make_metrics_config(),
                force=False,
            )
            self._observability_initialized = ok
            return ok

        except Exception as exc:
            LOGGER.exception("Observability initialization failed: %s", exc)
            return False

    def shutdown_observability(self) -> None:
        if not self._observability_initialized:
            return

        try:
            shutdown_observability(
                close_logging=True,
                shutdown_tracing=True,
                set_gauges_down=True,
            )
        finally:
            self._observability_initialized = False

    # --------------------------------------------------------------------------
    # Properties
    # --------------------------------------------------------------------------
    @property
    def time_provider(self) -> TimeProviderPort:
        return self._time_provider


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Composition Root                                                           │
# ╰────────────────────────────────────────────────────────────────────────────╯
def compose_runtime(
    *, root: str | None = None, env_file: str | None = None
) -> QuantumRuntime:
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
    mt5_settings = ConfigManager.load_mt5_cached()

    return QuantumRuntime(
        core_settings=core,
        logging_settings=logging_settings,
        tracing_settings=tracing_settings,
        mt5_settings=mt5_settings,
        time_provider=SystemTimeProviderAdapter(),
    )
