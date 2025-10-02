import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from opentelemetry import trace
from prometheus_client import Counter, Histogram

from quantum.shared.correlation.correlation_id import (
    correlation_context,
    new_correlation_id,
)

P = ParamSpec("P")
R = TypeVar("R")

_TRACER = trace.get_tracer("quantum.ui")

ui_actions_total = Counter(
    "quantum_ui_actions_total",
    "UI actions",
    ["action"],
)

ui_action_latency_ms = Histogram(
    "quantum_ui_action_latency_ms",
    "Latency of UI actions (ms)",
    buckets=(10, 25, 50, 100, 200, 400, 800, 1600, 3200),
)

ui_page_render_ms = Histogram(
    "quantum_ui_page_render_ms",
    "Page render duration (ms)",
    buckets=(10, 25, 50, 100, 200, 400, 800, 1600, 3200),
)


def ui_action(name: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def deco(fn: Callable[P, R]) -> Callable[P, R]:
        @wraps(fn)
        def _inner(*args: P.args, **kwargs: P.kwargs) -> R:
            cid = new_correlation_id()
            start = time.monotonic_ns()
            with (
                correlation_context(cid),
                _TRACER.start_as_current_span(f"ui.action.{name}"),
            ):
                try:
                    return fn(*args, **kwargs)
                finally:
                    dur_ms = (time.monotonic_ns() - start) // 1_000_000
                    ui_actions_total.labels(name).inc()
                    ui_action_latency_ms.observe(dur_ms)
                    logging.getLogger("quantum.ui").info(
                        "ui action completed",
                        extra={"attrs": {"ui.action": name, "ui.latency_ms": dur_ms}},
                    )

        return _inner

    return deco


class PageTimer:
    def __enter__(self):
        self._start = time.monotonic_ns()
        return self

    def __exit__(self, exc_type, exc, tb):
        dur_ms = (time.monotonic_ns() - self._start) // 1_000_000
        ui_page_render_ms.observe(dur_ms)
        logging.getLogger("quantum.ui").info(
            "ui page rendered", extra={"attrs": {"ui.render_ms": dur_ms}}
        )
