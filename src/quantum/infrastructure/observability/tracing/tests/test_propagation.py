from __future__ import annotations

import uuid

from contextlib import contextmanager

import pytest

from opentelemetry import baggage
from opentelemetry import context as otel_context
from opentelemetry.propagate import get_global_textmap

from quantum.infrastructure.observability.context.run_id import (
    get_run_id,
    run_id_context,
)
from quantum.infrastructure.observability.tracing.correlation.correlation_id import (
    correlation_context,
    get_correlation_id,
)
from quantum.infrastructure.observability.tracing.propagation import (
    baggage_context_from_ids,
    capture_context_snapshot,
    detach_process_baggage_if_any,
    install_process_baggage,
    setup_propagation,
    use_context_snapshot,
    wrap_callable_with_context,
)


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Helpers                                                                    │
# ╰────────────────────────────────────────────────────────────────────────────╯
def _baggage(key: str) -> str | None:
    """Safely read a baggage item from the current OTel context."""
    try:
        return baggage.get_baggage(key, context=otel_context.get_current())
    except Exception:
        return None


@contextmanager
def _ids_ctx(run_id: str, corr_id: str):
    """
    Context manager to temporarily set run_id and correlation_id ContextVars.
    Restores the previous values upon exit.
    """
    rc = run_id_context(run_id)
    cc = correlation_context(corr_id)
    rc.__enter__()
    cc.__enter__()
    try:
        yield
    finally:
        cc.__exit__(None, None, None)
        rc.__exit__(None, None, None)


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Tests                                                                      │
# ╰────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.unit
def test_setup_propagation_sets_composite_propagator():
    """
    Given setup_propagation()
    When invoked
    Then the global propagator is a composite (traceparent + baggage)
    """
    setup_propagation()
    prop = get_global_textmap()
    # No tight coupling to the class; assert on the type name only
    assert "CompositePropagator" in type(prop).__name__


@pytest.mark.unit
def test_install_and_detach_process_baggage_idempotent():
    """
    Given install_process_baggage(run_id, correlation_id)
    When called twice without a detach
    Then the second call is a NO-OP (does not overwrite values)
    And detach_process_baggage_if_any() removes the keys from baggage
    """
    # Ensure a clean initial state (in case another test left baggage attached)
    detach_process_baggage_if_any()

    rid1 = str(uuid.uuid4())
    cid1 = str(uuid.uuid4())
    install_process_baggage(run_id=rid1, correlation_id=cid1)

    assert _baggage("run_id") == rid1
    assert _baggage("correlation_id") == cid1

    # Idempotence: second call with different values must not overwrite
    rid2 = str(uuid.uuid4())
    cid2 = str(uuid.uuid4())
    install_process_baggage(run_id=rid2, correlation_id=cid2)

    assert _baggage("run_id") == rid1
    assert _baggage("correlation_id") == cid1

    # Detach → keys removed
    detach_process_baggage_if_any()
    assert _baggage("run_id") in (None, "")
    assert _baggage("correlation_id") in (None, "")


@pytest.mark.unit
def test_baggage_context_from_ids_temporarily_sets_keys():
    """
    Given baggage_context_from_ids()
    When run_id/correlation_id are present in ContextVars
    Then the manager injects them into OTel baggage during the block
    And restores the previous baggage afterwards
    """
    rid = str(uuid.uuid4())
    cid = str(uuid.uuid4())

    # Pre-condition: no baggage attached
    detach_process_baggage_if_any()
    assert _baggage("run_id") in (None, "")
    assert _baggage("correlation_id") in (None, "")

    with _ids_ctx(rid, cid):
        # Inside the manager: ContextVars → baggage projection
        with baggage_context_from_ids():
            assert _baggage("run_id") == rid
            assert _baggage("correlation_id") == cid
        # After exit: no baggage left from this manager
        assert _baggage("run_id") in (None, "")
        assert _baggage("correlation_id") in (None, "")


@pytest.mark.unit
def test_capture_and_use_context_snapshot_with_baggage_injection():
    """
    Given capture_context_snapshot() and use_context_snapshot(..., attach_otel=False, ensure_baggage_from_ids=True)
    When entering the snapshot context
    Then run_id/correlation_id are restored from the snapshot and also pushed to baggage
    And upon exit, the caller context is restored and baggage is cleared
    """
    rid1 = str(uuid.uuid4())
    cid1 = str(uuid.uuid4())
    with _ids_ctx(rid1, cid1):
        snap = capture_context_snapshot()

    # Change the current context to ensure the snapshot wins inside the block
    rid2 = str(uuid.uuid4())
    cid2 = str(uuid.uuid4())
    with _ids_ctx(rid2, cid2):
        # Before: current context ≠ snapshot
        assert get_run_id() == rid2 and get_correlation_id() == cid2
        assert _baggage("run_id") in (None, "")
        assert _baggage("correlation_id") in (None, "")

        # Inside: snapshot IDs visible + baggage injected from ContextVars
        with use_context_snapshot(
            snap, attach_otel=False, ensure_baggage_from_ids=True
        ):
            assert get_run_id() == rid1
            assert get_correlation_id() == cid1
            assert _baggage("run_id") == rid1
            assert _baggage("correlation_id") == cid1

        # After: caller context restored (rid2/cid2) and no baggage
        assert get_run_id() == rid2
        assert get_correlation_id() == cid2
        assert _baggage("run_id") in (None, "")
        assert _baggage("correlation_id") in (None, "")


@pytest.mark.unit
def test_wrap_callable_with_context_runs_under_snapshot():
    """
    Given wrap_callable_with_context()
    When wrapping a function and running it
    Then the function observes the snapshot context and baggage
    And the caller context remains intact after execution
    """
    rid_snap = str(uuid.uuid4())
    cid_snap = str(uuid.uuid4())
    with _ids_ctx(rid_snap, cid_snap):
        # Capture a snapshot with baggage attached
        with baggage_context_from_ids():
            snap = capture_context_snapshot()

    rid_cur = str(uuid.uuid4())
    cid_cur = str(uuid.uuid4())
    with _ids_ctx(rid_cur, cid_cur):
        # A callable that reads current IDs and baggage
        def _whoami():
            return (
                get_run_id(),
                get_correlation_id(),
                _baggage("run_id"),
                _baggage("correlation_id"),
            )

        wrapped = wrap_callable_with_context(_whoami, snap=snap)
        r_run_id, r_corr_id, b_rid, b_cid = wrapped()

        # During execution, the snapshot is visible
        assert r_run_id == rid_snap and r_corr_id == cid_snap
        # Wrapper uses use_context_snapshot with ensure_baggage_from_ids=True by default
        assert b_rid == rid_snap and b_cid == cid_snap

        # Caller context and baggage are intact afterwards
        assert get_run_id() == rid_cur and get_correlation_id() == cid_cur
        assert _baggage("run_id") in (None, "")
        assert _baggage("correlation_id") in (None, "")
