from contextlib import contextmanager
from contextvars import Token

from opentelemetry import baggage
from opentelemetry import context as otel_context
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.context.context import Context
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from quantum.shared.context.run_id import get_run_id
from quantum.shared.correlation.correlation_id import get_correlation_id

_PROCESS_BAGGAGE_TOKEN: Token[Context] | None = None


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
