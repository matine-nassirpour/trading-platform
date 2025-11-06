import threading
from collections.abc import Callable, Iterator
from concurrent.futures import Executor, Future
from contextlib import contextmanager
from contextvars import Token
from dataclasses import dataclass
from typing import TypeVar

from opentelemetry import baggage
from opentelemetry import context as otel_context
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.context.context import Context as OTelContext
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from quantum.infrastructure.observability.context.run_id import (
    get_run_id,
    run_id_context,
)
from quantum.infrastructure.observability.tracing.correlation.correlation_id import (
    correlation_context,
    get_correlation_id,
)

_PROCESS_BAGGAGE_TOKEN: Token[OTelContext] | None = None
T = TypeVar("T")


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Propagators (process-wide)                                                 │
# ╰────────────────────────────────────────────────────────────────────────────╯
def setup_propagation() -> None:
    """
    Configures W3C propagators (traceparent + baggage).
    Does NOT modify the global baggage: the process-wide attachment is handled separately.
    """
    set_global_textmap(
        CompositePropagator([TraceContextTextMapPropagator(), W3CBaggagePropagator()])
    )


def install_process_baggage(
    *, run_id: str | None = None, correlation_id: str | None = None
) -> None:
    """
    Attaches the baggage {run_id, correlation_id} to the process context **once only**.
    Idempotent: If already attached, does nothing.
    Use in bootstrap after generating IDs.
    """
    global _PROCESS_BAGGAGE_TOKEN
    if _PROCESS_BAGGAGE_TOKEN is not None:
        return

    rid = run_id or get_run_id()
    cid = correlation_id or get_correlation_id()
    if not rid and not cid:
        return

    ctx = otel_context.get_current()
    if rid:
        ctx = baggage.set_baggage("run_id", rid, context=ctx)
    if cid:
        ctx = baggage.set_baggage("correlation_id", cid, context=ctx)

    _PROCESS_BAGGAGE_TOKEN = otel_context.attach(ctx)


def detach_process_baggage_if_any() -> None:
    """
    Detach the process-wide baggage if installed.
    Safe to call multiple times.
    """
    global _PROCESS_BAGGAGE_TOKEN
    if _PROCESS_BAGGAGE_TOKEN is None:
        return
    try:
        otel_context.detach(_PROCESS_BAGGAGE_TOKEN)
    finally:
        _PROCESS_BAGGAGE_TOKEN = None


def refresh_process_baggage(
    *, run_id: str | None = None, correlation_id: str | None = None
) -> None:
    """
    Cleanly replaces the process-wide baggage (detach then install).
    Avoid in the hot path: favor local context managers.
    """
    detach_process_baggage_if_any()
    install_process_baggage(run_id=run_id, correlation_id=correlation_id)


@contextmanager
def baggage_context_from_ids():
    """
    Practical context for (re)injecting run_id / correlation_id into Baggage
    during a block (e.g., outgoing network call, ad-hoc job).
    """
    rid = get_run_id()
    cid = get_correlation_id()
    ctx = otel_context.get_current()
    if rid:
        ctx = baggage.set_baggage("run_id", rid, context=ctx)
    if cid:
        ctx = baggage.set_baggage("correlation_id", cid, context=ctx)
    token = otel_context.attach(ctx)
    try:
        yield
    finally:
        otel_context.detach(token)


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Explicit multi-thread context propagation                                  │
# │ (No implicit inheritance across threads — contract made explicit)          │
# ╰────────────────────────────────────────────────────────────────────────────╯
@dataclass(frozen=True)
class ContextSnapshot:
    """
    Lightweight snapshot of the current execution context:

    - otel: OpenTelemetry Context (trace context + baggage)
    - run_id / correlation_id: app-level IDs (ContextVar)
    """

    otel: OTelContext | None
    run_id: str | None
    correlation_id: str | None


def capture_context_snapshot() -> ContextSnapshot:
    """
    Capture the current OTel Context and app-level IDs.
    Safe to call in any thread; the snapshot is immutable and thread-safe.
    """
    return ContextSnapshot(
        otel=otel_context.get_current(),
        run_id=get_run_id(),
        correlation_id=get_correlation_id(),
    )


@contextmanager
def use_context_snapshot(
    snap: ContextSnapshot,
    *,
    attach_otel: bool = True,
    ensure_baggage_from_ids: bool = True,
) -> Iterator[None]:
    """
    Attach a captured snapshot to the current thread for the duration of the block.

    - attach_otel: attach the captured OTel Context (trace + baggage).
    - ensure_baggage_from_ids: if attach_otel is False or snap.otel is None,
      inject baggage from app IDs to keep {run_id, correlation_id} consistent.

    Also sets app ContextVars (run_id/correlation_id) for the duration.
    """
    # App ContextVars (enter/exit via their own context managers)
    rid_cm = run_id_context(snap.run_id) if snap.run_id else None
    cid_cm = correlation_context(snap.correlation_id) if snap.correlation_id else None

    otel_token: Token[OTelContext] | None = None
    baggage_cm = None

    try:
        if rid_cm:
            rid_cm.__enter__()
        if cid_cm:
            cid_cm.__enter__()

        if attach_otel and snap.otel is not None:
            otel_token = otel_context.attach(snap.otel)
        elif ensure_baggage_from_ids:
            # Ensure baggage keys exist even without full OTel context attach.
            baggage_cm = baggage_context_from_ids()
            baggage_cm.__enter__()

        yield
    finally:
        if otel_token is not None:
            otel_context.detach(otel_token)
        if baggage_cm is not None:
            baggage_cm.__exit__(None, None, None)
        if cid_cm:
            cid_cm.__exit__(None, None, None)
        if rid_cm:
            rid_cm.__exit__(None, None, None)


def run_in_context(snap: ContextSnapshot, fn: Callable[[], T]) -> T:
    """
    Run a no-arg callable under a given snapshot (helpers for thread entrypoints).
    """
    with use_context_snapshot(snap):
        return fn()


class ContextPropagatingThread(threading.Thread):
    """
    Thread that propagates the parent thread's context snapshot to the child thread.

    Usage:
        snap = capture_context_snapshot()  # in parent thread
        t = ContextPropagatingThread(target=fn, args=(...), snapshot=snap)
        t.start(); t.join()
    """

    def __init__(
        self,
        *args,
        snapshot: ContextSnapshot | None = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        # If no snapshot provided, capture at construction time (parent thread).
        self._snapshot = snapshot or capture_context_snapshot()

    def run(self) -> None:
        target = getattr(self, "_target", None)
        if target is None:
            return
        # Re-bind context for the lifetime of this thread execution.
        with use_context_snapshot(self._snapshot):
            target(*getattr(self, "_args", ()), **getattr(self, "_kwargs", {}))


def wrap_callable_with_context(
    fn: Callable[..., T],
    snap: ContextSnapshot | None = None,
) -> Callable[..., T]:
    """
    Wrap any callable so that, when invoked (e.g. by an executor worker),
    it runs under the provided (or captured) snapshot.
    """
    snapshot = snap or capture_context_snapshot()

    def _wrapped(*args, **kwargs) -> T:
        with use_context_snapshot(snapshot):
            return fn(*args, **kwargs)

    return _wrapped


def submit_with_context(
    executor: Executor,
    fn: Callable[..., T],
    *args,
    snapshot: ContextSnapshot | None = None,
    **kwargs,
) -> Future[T]:
    """
    Submit a task to a concurrent.futures.Executor while propagating context.
    The snapshot is captured at submit-time if not provided.
    """
    wrapped = wrap_callable_with_context(fn, snap=snapshot)
    return executor.submit(wrapped, *args, **kwargs)
