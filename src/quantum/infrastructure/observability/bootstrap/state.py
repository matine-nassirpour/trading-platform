"""
Global runtime state for the Quantum observability bootstrap layer.

This module holds shared references (e.g., the active OpenTelemetry
TracerProvider) that must persist across subsystems such as:

    • tracing.provider
    • tracing.lifecycle
    • bootstrap.init_manager
"""

from __future__ import annotations

from typing import Any

_tracer_provider_ref: Any | None = None


def set_tracer_provider(provider: Any | None) -> None:
    """
    Register or clear the active tracer provider reference.

    This is called once during initialization (via provider.init_tracing).
    The function is idempotent and safe to call multiple times.
    """
    global _tracer_provider_ref
    _tracer_provider_ref = provider


def get_tracer_provider() -> Any | None:
    """
    Retrieve the active tracer provider reference, if any.

    Used by LifecycleService and other observability subsystems
    for coordinated shutdown and state inspection.
    """
    return _tracer_provider_ref
