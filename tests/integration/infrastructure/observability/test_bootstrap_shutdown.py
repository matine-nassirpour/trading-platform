# tests/integration/infrastructure/observability/test_bootstrap_shutdown.py
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, cast

import pytest

_NumberLike = float | int | str | bytes


def _gauge_value(g: Any) -> float:
    """Reads the value of a prometheus_client Gauge/Counter (fixture-isolated registry)."""
    maybe_get = getattr(getattr(g, "_value", None), "get", None)
    if not callable(maybe_get):
        return -1.0
    try:
        return float(cast(Callable[[], _NumberLike], maybe_get)())
    except Exception:
        return -1.0


def _root_handlers():
    return list(logging.getLogger().handlers)


def _audit_handlers():
    return list(logging.getLogger("quantum.trading").handlers)


@pytest.mark.usefixtures("no_rate_limit_no_sampling")
def test_bootstrap_shutdown_idempotence_and_cleanup(tmp_workspace):
    """
    Contractual objectives:

    1. Two successive init_observability() (without force) are idempotent:
        - no duplication of handlers
        - same handler objects (identity) retained
    2. shutdown_observability(set_gauges_down=True):
        - no more handlers attached to the affected loggers
        - health gauges reset to 0
    """
    from quantum.infrastructure.observability.init_observability import (
        init_observability,
        shutdown_observability,
    )
    from quantum.infrastructure.observability.logging.logs import (
        close_and_remove_all_handlers as _close_handlers,
    )
    from quantum.infrastructure.observability.metrics import health as m

    # First init: pipeline up
    init_observability()  # force=False by default

    root_h1 = _root_handlers()
    audit_h1 = _audit_handlers()

    # Sanity: we must have at least the console + (optional) the partitioned file handler
    assert len(root_h1) >= 1, "root logger should have at least one handler after init"
    # The audit handler is present if QUANTUM_AUDIT_DIR is defined (this is the case via tmp_workspace)
    assert (
        len(audit_h1) >= 1
    ), "audit logger should have at least one handler after init"

    # Gauges de santé à 1
    assert _gauge_value(m.pipeline_logging_ok) == 1.0
    assert _gauge_value(m.pipeline_tracing_ok) == 1.0
    assert _gauge_value(m.logging_sink_up) == 1.0
    assert _gauge_value(m.pipeline_up) == 1.0

    # Second init (without force): idempotence → no new handlers
    init_observability()  # idempotent branch: early return

    root_h2 = _root_handlers()
    audit_h2 = _audit_handlers()

    # Same number…
    assert len(root_h2) == len(
        root_h1
    ), "root handlers count changed on idempotent init"
    assert len(audit_h2) == len(
        audit_h1
    ), "audit handlers count changed on idempotent init"
    # …and same objects (identity)
    assert [id(h) for h in root_h2] == [
        id(h) for h in root_h1
    ], "root handlers were replaced on idempotent init"
    assert [id(h) for h in audit_h2] == [
        id(h) for h in audit_h1
    ], "audit handlers were replaced on idempotent init"

    # Shutdown with gauge reset + handler cleaning
    shutdown_observability(
        close_logging=True,
        shutdown_tracing=True,
        reset_state=True,
        set_gauges_down=True,
    )

    # No more handlers attached
    assert _root_handlers() == [], "root logger should have no handlers after shutdown"

    _close_handlers(logging.getLogger("quantum.trading"))
    assert (
        _audit_handlers() == []
    ), "audit logger should have no handlers after shutdown"

    # Gauges at 0
    assert _gauge_value(m.pipeline_up) == 0.0, "pipeline_up should be 0 after shutdown"
    # These gauges can raise if the lib/registry is unmounted; conftest isolates REGISTRY → testable:
    assert (
        _gauge_value(m.logging_sink_up) == 0.0
    ), "logging_sink_up should be 0 after shutdown"
    assert (
        _gauge_value(m.otel_tracing_up) == 0.0
    ), "otel_tracing_up should be 0 after shutdown"

    # Re-init after shutdown (cleaning OK → pipeline restarts properly)
    init_observability()

    # Handlers recreated
    root_h3 = _root_handlers()
    audit_h3 = _audit_handlers()
    assert len(root_h3) >= 1, "root handlers not re-created after re-init"
    assert len(audit_h3) >= 1, "audit handlers not re-created after re-init"

    # Gauges back to 1
    assert _gauge_value(m.pipeline_up) == 1.0
    assert _gauge_value(m.pipeline_logging_ok) == 1.0
    assert _gauge_value(m.pipeline_tracing_ok) == 1.0
