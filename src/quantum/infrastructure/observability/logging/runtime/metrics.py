from __future__ import annotations

from collections.abc import Callable
from contextlib import suppress

from quantum.infrastructure.observability.logging.runtime.diagnostics import (
    get_diagnostic_logger,
)

_logger = get_diagnostic_logger()


class Counter:
    """Dependency-free counter used only for internal observability health."""

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
            with suppress(Exception):
                _logger.error(f"[C0-metrics] failed to increment '{self._name}'")


# global registry (optional)
_internal_metrics: dict[str, Counter] = {}


def define_counter(
    name: str,
    inc_func: Callable[[int], None] | None = None,
) -> Counter:
    cnt = Counter(name, inc_func)
    _internal_metrics[name] = cnt
    return cnt
