from __future__ import annotations

from quantum.infrastructure.observability.bootstrap.health_registry import (
    HealthRegistry,
)
from quantum.infrastructure.observability.bootstrap.init_diagnostics import (
    BootstrapDiagnostics,
)
from quantum.infrastructure.observability.runtime.runtime_context import (
    _RuntimeContextHolder,
)


def get_health_registry() -> HealthRegistry:
    """Public read-only accessor used by dashboards (Streamlit)."""
    return _RuntimeContextHolder.get().health


def get_diagnostics() -> BootstrapDiagnostics:
    """Public read-only accessor used by dashboards."""
    return _RuntimeContextHolder.get().diagnostics
