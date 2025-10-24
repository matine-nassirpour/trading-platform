from __future__ import annotations

import logging

import pytest

from tests.support.logging_utils import counter_value


def _root_handlers() -> list[logging.Handler]:
    return list(logging.getLogger().handlers)


def _audit_handlers() -> list[logging.Handler]:
    return list(logging.getLogger("quantum.trading").handlers)


@pytest.mark.usefixtures("no_rate_limit_no_sampling")
def test_bootstrap_shutdown_idempotence_and_cleanup(tmp_workspace):
    """
    Contract:

    1) Two successive init_observability() (without force) are idempotent:
       - no handler duplication
       - same handler objects (identity) retained

    2) shutdown_observability(set_gauges_down=True):
       - no more handlers attached to the affected loggers
       - health gauges reset to 0
    """
    from quantum.infrastructure.observability.bootstrap.init_manager import (
        init_observability,
        shutdown_observability,
    )
    from quantum.infrastructure.observability.logging.service import (
        close_and_remove_all_handlers as _close_handlers,
    )
    from quantum.infrastructure.observability.metrics.collectors import (
        health_collector as m,
    )

    # First init: pipeline up
    init_observability()  # force=False by default

    root_h1 = _root_handlers()
    audit_h1 = _audit_handlers()

    # Sanity: at least console (+ optional file handler)
    assert len(root_h1) >= 1, "root logger should have at least one handler after init"
    assert (
        len(audit_h1) >= 1
    ), "audit logger should have at least one handler after init"

    # Health gauges = 1
    assert counter_value(m.pipeline_logging_ok) == 1.0
    assert counter_value(m.pipeline_tracing_ok) == 1.0
    assert counter_value(m.logging_sink_up) == 1.0
    assert counter_value(m.pipeline_up) == 1.0

    # Second init (without force) must be idempotent → no new handlers
    init_observability()  # idempotent path

    root_h2 = _root_handlers()
    audit_h2 = _audit_handlers()

    assert len(root_h2) == len(
        root_h1
    ), "root handlers count changed on idempotent init"
    assert len(audit_h2) == len(
        audit_h1
    ), "audit handlers count changed on idempotent init"

    # Same handler objects (identity)
    assert [id(h) for h in root_h2] == [
        id(h) for h in root_h1
    ], "root handlers replaced"
    assert [id(h) for h in audit_h2] == [
        id(h) for h in audit_h1
    ], "audit handlers replaced"

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
    assert counter_value(m.pipeline_up) == 0.0, "pipeline_up should be 0 after shutdown"
    assert (
        counter_value(m.logging_sink_up) == 0.0
    ), "logging_sink_up should be 0 after shutdown"
    assert (
        counter_value(m.otel_tracing_up) == 0.0
    ), "otel_tracing_up should be 0 after shutdown"

    # Re-init after shutdown — pipeline restarts properly
    init_observability()
    root_h3 = _root_handlers()
    audit_h3 = _audit_handlers()
    assert len(root_h3) >= 1, "root handlers not re-created after re-init"
    assert len(audit_h3) >= 1, "audit handlers not re-created after re-init"

    # Gauges back to 1
    assert counter_value(m.pipeline_up) == 1.0
    assert counter_value(m.pipeline_logging_ok) == 1.0
    assert counter_value(m.pipeline_tracing_ok) == 1.0
