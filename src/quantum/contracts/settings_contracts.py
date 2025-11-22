"""
Quantum Core Configuration Contracts — Settings Models
──────────────────────────────────────────────────────
Defines stable interfaces (protocols) describing the expected structure
and invariants of all configuration models within the Quantum platform.

Responsibilities
----------------
- Declare the structural contracts of all configuration models.
- Provide type-safe interfaces for testing and runtime introspection.
- Guarantee forward compatibility across future model refactors.
- Serve as the canonical definition of configuration invariants.

Design Principles
-----------------
- **Single Responsibility** : declares expected attributes and invariants.
- **Liskov Substitution** : any concrete model must satisfy these contracts.
- **Clean Architecture** : no dependency on Pydantic or runtime logic.
- **Stability** : remains invariant across model refactors.
- **Transparency** : provides explicit, type-safe configuration expectations.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, runtime_checkable


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Base Settings Contract                                                     │
# ╰────────────────────────────────────────────────────────────────────────────╯
@runtime_checkable
class BaseSettingsContract(Protocol):
    """
    Base contract implemented by all Quantum configuration models.

    Ensures a consistent and minimal public interface for serialization
    and safe exposure of configuration data.
    """

    def model_dump(self) -> Mapping[str, object]:
        """Return the model as a plain dictionary (no secrets filtering)."""
        ...

    def to_public_dict(self) -> dict[str, str]:
        """Return a sanitized, non-sensitive subset for logs or diagnostics."""
        ...


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Core Settings Contract                                                     │
# ╰────────────────────────────────────────────────────────────────────────────╯
@runtime_checkable
class CoreSettingsContract(BaseSettingsContract, Protocol):
    """Contract for the platform runtime configuration model."""

    quantum_app_name: str
    quantum_app_version: str
    quantum_env: str
    quantum_ns: str
    quantum_instance_id: str | None
    quantum_metrics_addr: str
    quantum_metrics_port: int
    quantum_exec_timeout: float
    quantum_exec_retries: int
    quantum_exec_backoff: float
    quantum_exec_backoff_max: float


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Logging Settings Contract                                                  │
# ╰────────────────────────────────────────────────────────────────────────────╯
@runtime_checkable
class LoggingSettingsContract(BaseSettingsContract, Protocol):
    """Contract for the logging configuration model."""

    quantum_log_level: str
    quantum_log_sample_info: int
    quantum_log_ratelimit: bool
    quantum_log_rps: int
    quantum_log_fsync: bool
    quantum_log_max_bytes: int
    quantum_log_warn_bytes: int
    quantum_log_dir: str | None
    quantum_audit_dir: str | None
    quantum_audit_allowlist: str | None
    streamlit_log_tz: str
    streamlit_log_renderer: str
    streamlit_log_expanded: bool
    streamlit_log_chunk_bytes: int
    streamlit_log_tail_max_lines: int
    streamlit_log_glob: str


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Tracing Settings Contract                                                  │
# ╰────────────────────────────────────────────────────────────────────────────╯
@runtime_checkable
class TracingSettingsContract(BaseSettingsContract, Protocol):
    """Contract for the tracing and telemetry configuration model."""

    quantum_trace_exporter: str
    quantum_trace_otlp_endpoint: str
    quantum_trace_otlp_protocol: str
    quantum_trace_otlp_headers: str | None
    quantum_trace_otlp_timeout_ms: int
    quantum_trace_otlp_compression: str
    quantum_trace_otlp_insecure: bool
    quantum_trace_sample: float


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ MT5 Settings Contract                                                      │
# ╰────────────────────────────────────────────────────────────────────────────╯
@runtime_checkable
class MT5SettingsContract(BaseSettingsContract, Protocol):
    """Contract for MetaTrader 5 broker and terminal configuration."""

    quantum_mt5_ftmo_login: int | None
    quantum_mt5_ftmo_server: str | None
    quantum_mt5_ftmo_password: str | None
    quantum_mt5_fundednext_login: int | None
    quantum_mt5_fundednext_server: str | None
    quantum_mt5_fundednext_password: str | None
    mt5_ftmo_terminal_path: str | None
    mt5_fundednext_terminal_path: str | None
