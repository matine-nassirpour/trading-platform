import threading

from collections.abc import Callable, Iterator
from concurrent.futures import Executor, Future
from contextlib import AbstractContextManager, contextmanager
from contextvars import Token
from dataclasses import dataclass
from typing import Any, TypeVar

from opentelemetry import baggage
from opentelemetry import context as otel_context
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.context.context import Context as OTelContext
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from quantum.infrastructure.observability.context.context_attributes_provider import (
    ContextAttributesProvider,
)
from quantum.infrastructure.observability.context.correlation_id import (
    correlation_context,
)
from quantum.infrastructure.observability.context.run_id import run_id_context

T = TypeVar("T")
_PROCESS_BAGGAGE_TOKEN: Token[OTelContext] | None = None


# --- Propagators (process-wide)
def setup_propagation() -> None:
    """
    Configure global W3C propagators (traceparent + baggage).
    Does not attach baggage; only registers the propagators.
    """
    set_global_textmap(
        CompositePropagator([TraceContextTextMapPropagator(), W3CBaggagePropagator()])
    )


def install_process_baggage(
    *, run_id: str | None = None, correlation_id: str | None = None
) -> None:
    """
    Attaches process-wide baggage (run_id, correlation_id) exactly once.
    Idempotent: repeated calls are ignored.
    """
    global _PROCESS_BAGGAGE_TOKEN
    if _PROCESS_BAGGAGE_TOKEN is not None:
        return

    ctx_attrs = ContextAttributesProvider.get()
    rid = run_id or ctx_attrs.run_id
    cid = correlation_id or ctx_attrs.correlation_id

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
    Detach process-wide baggage if installed.
    Safe, idempotent, never raises.
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
    Replace process-wide baggage atomically.
    Avoid using in hot path.
    """
    detach_process_baggage_if_any()
    install_process_baggage(run_id=run_id, correlation_id=correlation_id)


@contextmanager
def baggage_context_from_ids() -> Iterator[None]:
    """
    Construct OTel baggage for the current block based on C0 context.
    Useful for outgoing RPC calls / message publishing.
    """
    ctx_attrs = ContextAttributesProvider.get()
    rid = ctx_attrs.run_id
    cid = ctx_attrs.correlation_id

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


# --- Context Snapshot (Thread-Safe, Immutable)
@dataclass(frozen=True)
class ContextSnapshot:
    """
    Immutable snapshot of:
    - OTel Context (trace context + baggage)
    - Application context (C0: run_id, correlation_id)
    """

    otel: OTelContext | None
    run_id: str | None
    correlation_id: str | None


def capture_context_snapshot() -> ContextSnapshot:
    """
    Capture an immutable snapshot of both:
    - OTel context
    - C0 run_id / correlation_id
    """
    ctx_attrs = ContextAttributesProvider.get()
    return ContextSnapshot(
        otel=otel_context.get_current(),
        run_id=ctx_attrs.run_id,
        correlation_id=ctx_attrs.correlation_id,
    )


# --- Internal Helpers
def _enter_app_contexts(
    snap: ContextSnapshot,
) -> tuple[AbstractContextManager[None] | None, AbstractContextManager[None] | None]:
    """
    Enter run_id and correlation_id contexts locally.
    """
    rid_cm = run_id_context(snap.run_id) if snap.run_id else None
    cid_cm = correlation_context(snap.correlation_id) if snap.correlation_id else None

    if rid_cm:
        rid_cm.__enter__()
    if cid_cm:
        cid_cm.__enter__()

    return rid_cm, cid_cm


def _enter_otel_or_baggage(
    snap: ContextSnapshot,
    attach_otel: bool,
    ensure_baggage_from_ids: bool,
) -> tuple[Token[OTelContext] | None, AbstractContextManager[None] | None]:

    otel_token: Token[OTelContext] | None = None
    baggage_cm: AbstractContextManager[None] | None = None

    if attach_otel and snap.otel is not None:
        otel_token = otel_context.attach(snap.otel)
    elif ensure_baggage_from_ids:
        baggage_cm = baggage_context_from_ids()
        baggage_cm.__enter__()

    return otel_token, baggage_cm


def _exit_all_contexts(
    rid_cm: AbstractContextManager[None] | None,
    cid_cm: AbstractContextManager[None] | None,
    otel_token: Token[OTelContext] | None,
    baggage_cm: AbstractContextManager[None] | None,
) -> None:

    if otel_token is not None:
        otel_context.detach(otel_token)

    if baggage_cm is not None:
        baggage_cm.__exit__(None, None, None)

    if cid_cm:
        cid_cm.__exit__(None, None, None)

    if rid_cm:
        rid_cm.__exit__(None, None, None)


# --- Main ContextManager
@contextmanager
def use_context_snapshot(
    snap: ContextSnapshot,
    *,
    attach_otel: bool = True,
    ensure_baggage_from_ids: bool = True,
) -> Iterator[None]:
    """
    Apply a captured snapshot to current thread:
    - attach OTel context (optional)
    - attach C0 context (run_id, correlation_id)
    - fallback to baggage-only propagation if needed
    """
    rid_cm, cid_cm = _enter_app_contexts(snap)
    otel_token, baggage_cm = _enter_otel_or_baggage(
        snap=snap,
        attach_otel=attach_otel,
        ensure_baggage_from_ids=ensure_baggage_from_ids,
    )

    try:
        yield
    finally:
        _exit_all_contexts(rid_cm, cid_cm, otel_token, baggage_cm)


# --- Concurrency utilities
def run_in_context(snap: ContextSnapshot, fn: Callable[[], T]) -> T:
    with use_context_snapshot(snap):
        return fn()


class ContextPropagatingThread(threading.Thread):
    """
    Thread that inherits the parent's C0+OTel context snapshot.

    Usage:
        snap = capture_context_snapshot()
        t = ContextPropagatingThread(target=fn, snapshot=snap)
        t.start()
    """

    def __init__(
        self, *args: Any, snapshot: ContextSnapshot | None = None, **kwargs: Any
    ) -> None:
        super().__init__(*args, **kwargs)
        self._snapshot = snapshot or capture_context_snapshot()

    def run(self) -> None:
        target = getattr(self, "_target", None)
        if target is None:
            return

        with use_context_snapshot(self._snapshot):
            target(*getattr(self, "_args", ()), **getattr(self, "_kwargs", {}))


def wrap_callable_with_context(
    fn: Callable[..., T],
    snap: ContextSnapshot | None = None,
) -> Callable[..., T]:

    snapshot = snap or capture_context_snapshot()

    def _wrapped(*args: Any, **kwargs: Any) -> T:
        with use_context_snapshot(snapshot):
            return fn(*args, **kwargs)

    return _wrapped


def submit_with_context(
    executor: Executor,
    fn: Callable[..., T],
    *args: Any,
    snapshot: ContextSnapshot | None = None,
    **kwargs: Any,
) -> Future[T]:

    wrapped = wrap_callable_with_context(fn, snap=snapshot)
    return executor.submit(wrapped, *args, **kwargs)
