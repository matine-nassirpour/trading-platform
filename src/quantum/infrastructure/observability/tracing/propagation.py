from opentelemetry import baggage
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
    refresh_baggage_from_context()


def refresh_baggage_from_context() -> None:
    rid = get_run_id()
    cid = get_correlation_id()
    if rid:
        baggage.set_baggage("run_id", rid)
    if cid:
        baggage.set_baggage("correlation_id", cid)
