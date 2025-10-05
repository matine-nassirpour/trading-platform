from contextlib import contextmanager

from opentelemetry import baggage
from opentelemetry import context as otel_context
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from quantum.shared.context.run_id import get_run_id
from quantum.shared.correlation.correlation_id import get_correlation_id


def setup_propagation() -> None:
    set_global_textmap(
        CompositePropagator([TraceContextTextMapPropagator(), W3CBaggagePropagator()])
    )
    # Option: we attach the IDs present at startup for the first time
    refresh_baggage_from_context()


def refresh_baggage_from_context() -> None:
    rid = get_run_id()
    cid = get_correlation_id()
    ctx = otel_context.get_current()
    if rid:
        ctx = baggage.set_baggage("run_id", rid, context=ctx)
    if cid:
        ctx = baggage.set_baggage("correlation_id", cid, context=ctx)
    # Attach the new enriched context (no detach here: we apply it globally)
    otel_context.attach(ctx)


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
