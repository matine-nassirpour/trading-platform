import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from opentelemetry import trace
from opentelemetry.trace import get_current_span
from prometheus_client import Counter, Histogram

from quantum.infrastructure.observability.tracing.propagation import (
    baggage_context_from_ids,
)
from quantum.shared.correlation.correlation_id import (
    correlation_context,
    new_correlation_id,
)

P = ParamSpec("P")
R = TypeVar("R")

_TRACER = trace.get_tracer("quantum.ui")


ui_action_latency_seconds = Histogram(
    "quantum_ui_action_latency_seconds",
    "Latency of UI actions (seconds)",
    ["action"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.2, 0.4, 0.8, 1.6, 3.2, 6.4),
)

ui_page_render_seconds = Histogram(
    "quantum_ui_page_render_seconds",
    "Page render duration (seconds)",
    buckets=(0.01, 0.025, 0.05, 0.1, 0.2, 0.4, 0.8, 1.6, 3.2, 6.4),
)

ui_actions_total = Counter(
    "quantum_ui_actions_total",
    "UI actions",
    ["action"],
)


def _current_exemplar() -> dict | None:
    sc = get_current_span().get_span_context()
    if getattr(sc, "is_valid", False):
        return {"trace_id": f"{sc.trace_id:032x}", "span_id": f"{sc.span_id:016x}"}
    return None


def ui_action(name: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def deco(fn: Callable[P, R]) -> Callable[P, R]:
        @wraps(fn)
        def _inner(*args: P.args, **kwargs: P.kwargs) -> R:
            cid = new_correlation_id()
            start = time.monotonic_ns()
            with correlation_context(cid):
                with baggage_context_from_ids():
                    with _TRACER.start_as_current_span(f"ui.action.{name}"):
                        try:
                            return fn(*args, **kwargs)
                        finally:
                            dur_ms = (time.monotonic_ns() - start) // 1_000_000
                            dur_s = dur_ms / 1000.0
                            ui_actions_total.labels(name).inc()
                            ex = _current_exemplar()
                            if ex:
                                try:
                                    ui_action_latency_seconds.labels(name).observe(
                                        dur_s, exemplar=ex
                                    )
                                except TypeError:
                                    ui_action_latency_seconds.labels(name).observe(
                                        dur_s
                                    )
                            logging.getLogger("quantum.ui").info(
                                "ui action completed",
                                extra={
                                    "attrs": {
                                        "ui.action": name,
                                        "ui.latency_ms": dur_ms,
                                    }
                                },
                            )

        return _inner

    return deco


class PageTimer:
    def __enter__(self):
        self._start = time.monotonic_ns()
        # Dedicated correlation for each rendering
        cid = new_correlation_id()
        self._corr_ctx = correlation_context(cid)
        self._corr_ctx.__enter__()
        self._baggage_cm = baggage_context_from_ids()
        self._baggage_cm.__enter__()
        self._span_cm = _TRACER.start_as_current_span("ui.page.render")
        self._span = self._span_cm.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb):
        dur_ms = (time.monotonic_ns() - self._start) // 1_000_000
        dur_s = dur_ms / 1000.0
        ex = _current_exemplar()
        if ex:
            try:
                ui_page_render_seconds.observe(dur_s, exemplar=ex)
            except TypeError:
                ui_page_render_seconds.observe(dur_s)

        logging.getLogger("quantum.ui").info(
            "ui page rendered", extra={"attrs": {"ui.render_ms": dur_ms}}
        )
        self._span_cm.__exit__(exc_type, exc, tb)
        self._baggage_cm.__exit__(exc_type, exc, tb)
        self._corr_ctx.__exit__(exc_type, exc, tb)
