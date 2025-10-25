"""
Global state for observability bootstrap
────────────────────────────────────────

Holds shared runtime references (e.g., the active TracerProvider)
that must persist across modules such as provider.py, lifecycle.py,
and init_manager.py.
"""

from __future__ import annotations

from typing import Any

_tracer_provider_ref: Any | None = None


def set_tracer_provider(tp: Any | None) -> None:
    """
    Register the active tracer provider reference.
    Called once by provider.init_tracing().
    """
    global _tracer_provider_ref
    _tracer_provider_ref = tp


def get_tracer_provider() -> Any | None:
    """
    Retrieve the active tracer provider reference.
    Used by LifecycleService for coordinated shutdown.
    """
    return _tracer_provider_ref
