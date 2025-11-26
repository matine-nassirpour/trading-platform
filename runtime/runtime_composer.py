"""
Quantum Runtime Composition Root

Responsibilities
----------------
- Load validated configuration models (Core/Logging/Tracing/MT5)
- Produce observability configs (logging/tracing/metrics)
- Bootstrap the Observability subsystem
- Return a QuantumRuntime instance (container only)

This module MUST NOT:
    - instantiate application services
    - instantiate event bus
    - instantiate runtime engine
    - import application/domain layers

It is purely an internal infrastructure composition root.
"""

from __future__ import annotations

import logging

from typing import Final

from quantum.infrastructure.config.models.core import CoreSettings
from quantum.infrastructure.config.models.logging import LoggingSettings
from quantum.infrastructure.config.models.tracing import TracingSettings
from quantum.infrastructure.config.runtime.manager import ConfigManager
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
        mt5_settings,
    ) -> None:
        self.core = core_settings
        self.logging_cfg = logging_settings
        self.tracing_cfg = tracing_settings
        self.mt5_cfg = mt5_settings

        self._observability_initialized = False

    # --------------------------------------------------------------------------
    # Adapters — convert Pydantic Settings → Observability Value Objects
    # --------------------------------------------------------------------------
    def _make_logging_config(self) -> LoggingConfig:
        s = self.logging_cfg
        c = self.core
        return LoggingConfig(
            environment=c.quantum_env,
            service_namespace=c.quantum_ns,
            service_name=c.quantum_app_name,
            service_version=c.quantum_app_version,
            instance_id=c.quantum_instance_id or "unknown",
            log_dir=s.quantum_log_dir,
            audit_dir=s.quantum_audit_dir,
            audit_allowlist=frozenset(
                x.strip()
                for x in (s.quantum_audit_allowlist or "").split(",")
                if x.strip()
            ),
            log_level=_parse_log_level(s.quantum_log_level),
            sample_info_every=s.quantum_log_sample_info,
            ratelimit_rps=float(s.quantum_log_rps),
            log_fsync=s.quantum_log_fsync,
            log_max_bytes=s.quantum_log_max_bytes,
            log_warn_bytes=s.quantum_log_warn_bytes,
        )

    def _make_tracing_config(self) -> TracingConfig:
        c = self.core
        s = self.tracing_cfg
        return TracingConfig(
            environment=c.quantum_env,
            service_namespace=c.quantum_ns,
            service_name=c.quantum_app_name,
            service_version=c.quantum_app_version,
            instance_id=c.quantum_instance_id or "unknown",
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
        c = self.core
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

    MUST NOT import domain/application directly.
    """
    # Load configuration using internal configuration framework
    core = ConfigManager.load(root, env_file=env_file, override=False, apply=False)
    env_dict = core.model_dump()

    logging_settings = ConfigManager.load_logging(env=env_dict)
    tracing_settings = ConfigManager.load_tracing(env=env_dict)
    mt5_settings = ConfigManager.load_mt5(env=env_dict)

    LOGGER.info(
        "Runtime configuration loaded",
        extra={"attrs": {"env": core.quantum_env, "app": core.quantum_app_name}},
    )

    return QuantumRuntime(
        core_settings=core,
        logging_settings=logging_settings,
        tracing_settings=tracing_settings,
        mt5_settings=mt5_settings,
    )
