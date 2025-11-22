from __future__ import annotations

from collections.abc import Callable
from contextlib import suppress

from quantum.infrastructure.observability.logging.runtime.diagnostics import (
    get_diagnostic_logger,
)

_logger = get_diagnostic_logger()


class Counter:
    """
    Pure C0 internal dependency-free counter.
    - No external dependencies (Prometheus, OTEL, …)
    - No global registration side effects beyond C0
    """

    __slots__ = ("_name", "_inc")

    def __init__(
        self,
        name: str,
        inc_func: Callable[[int], None] | None = None,
    ) -> None:
        self._name = name
        self._inc = inc_func or (lambda amount: None)

    def inc(self, amount: int = 1) -> None:
        try:
            self._inc(amount)
        except Exception:
            # Fail-safe, never raise
            with suppress(Exception):
                _logger.error(f"[C0-metrics] failed to increment '{self._name}'")


# Internal C0 registry
_internal_metrics: dict[str, Counter] = {}


def define_counter(
    name: str,
    inc_func: Callable[[int], None] | None = None,
) -> Counter:
    """
    Pure C0 factory.
    Registers a counter in the internal registry.
    No Prometheus / OTEL here (C1/C2 handle integration).
    """
    existing = _internal_metrics.get(name)
    if existing is not None:
        return existing

    cnt = Counter(name, inc_func)
    _internal_metrics[name] = cnt
    return cnt
