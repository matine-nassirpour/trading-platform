from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor

import pytest
from opentelemetry import trace

from quantum.infrastructure.observability.tracing.propagation import (
    ContextPropagatingThread,
    baggage_context_from_ids,
    capture_context_snapshot,
    submit_with_context,
)
from quantum.shared.correlation.correlation_id import (
    correlation_context,
    new_correlation_id,
)


@pytest.mark.usefixtures("no_rate_limit_no_sampling")
def test_context_propagation_threads_and_executor(
    obs_session, tmp_workspace, assert_jsonl_tail
):
    """
    Contract: Context propagation (OTel + ContextVars) works between threads and executors.

    Expectations:
        - Logs emitted under child spans in a thread and via an executor contain a valid trace_id/span_id (32/16 hex).

        - Child spans carry the 'quantum.run_id' and 'quantum.correlation_id' attributes injected by the enrichment SpanProcessor.
    """
    tracer = trace.get_tracer("quantum.test.ctx")
    log = logging.getLogger("ctx")

    # Parent context: create a correlation_id, inject it into baggage,
    # and open a parent span in the current thread.
    with correlation_context(new_correlation_id()):
        with baggage_context_from_ids():
            with tracer.start_as_current_span("ctx.parent"):
                # Capture a snapshot for explicit propagation.
                snap = capture_context_snapshot()

                # THREAD: execute a payload under ContextPropagatingThread
                thread_attrs_ok = {"ok": False}

                def _thread_target() -> None:
                    # Child span in thread
                    with tracer.start_as_current_span("ctx.thread.child") as sp:
                        # Check the presence of attributes on the span
                        attrs = getattr(sp, "attributes", {}) or {}
                        if (
                            "quantum.run_id" in attrs
                            and "quantum.correlation_id" in attrs
                            and attrs["quantum.correlation_id"]
                        ):
                            thread_attrs_ok["ok"] = True
                        # Log under child span → must have trace_id/span_id
                        log.info(
                            "inside thread child",
                            extra={"attrs": {"in_thread": True}},
                        )

                t = ContextPropagatingThread(target=_thread_target, snapshot=snap)
                t.start()
                t.join()

                # EXECUTOR: execute a payload via submit_with_context
                def _executor_fn() -> bool:
                    with tracer.start_as_current_span("ctx.exec.child") as sp:
                        attrs = getattr(sp, "attributes", {}) or {}
                        ok = (
                            "quantum.run_id" in attrs
                            and "quantum.correlation_id" in attrs
                            and bool(attrs.get("quantum.correlation_id"))
                        )
                        log.info(
                            "inside executor child",
                            extra={"attrs": {"in_executor": True}},
                        )
                        return bool(ok)

                with ThreadPoolExecutor(max_workers=1) as ex:
                    fut = submit_with_context(ex, _executor_fn, snapshot=snap)
                    exec_attrs_ok = fut.result()

    # Asserts on child spans (attributes present)
    assert (
        thread_attrs_ok["ok"] is True
    ), "child span in thread missing quantum.* attributes"
    assert exec_attrs_ok is True, "child span in executor missing quantum.* attributes"

    # Asserts on JSONL logs: presence of valid trace_id/span_id
    logs_dir = tmp_workspace["logs"]

    def _has_trace_ids(obj: dict) -> bool:
        tid = obj.get("trace_id")
        sid = obj.get("span_id")
        if not (isinstance(tid, str) and isinstance(sid, str)):
            return False
        return len(tid) == 32 and len(sid) == 16

    # log from the thread
    hits_thread = assert_jsonl_tail(
        logs_dir,
        match=lambda o: o.get("message") == "inside thread child" and _has_trace_ids(o),
        min_count=1,
    )
    # log from the executor
    hits_exec = assert_jsonl_tail(
        logs_dir,
        match=lambda o: o.get("message") == "inside executor child"
        and _has_trace_ids(o),
        min_count=1,
    )

    # Additional Sanity: Ensure that logs contain the marked attribute
    assert hits_thread[0]["attrs"].get("in_thread") is True
    assert hits_exec[0]["attrs"].get("in_executor") is True
