from __future__ import annotations

import threading

from collections.abc import Callable, Iterable
from contextlib import suppress

_METRICS_LOCK = threading.Lock()


class Counter:
    """
    Pure C0 internal dependency-free counter.
    - No external dependencies (Prometheus, OTEL, …)
    - No global registration side effects beyond C0
    """

    __slots__ = ("_name", "_hooks")

    def __init__(self, name: str) -> None:
        self._name = name
        self._hooks: list[Callable[[int], None]] = []

    # --------------------------------------------------------------------------
    # Public C0 API
    # --------------------------------------------------------------------------
    @property
    def name(self) -> str:
        """Stable identifier of the counter."""
        return self._name

    def inc(self, amount: int = 1) -> None:
        """
        Increment the counter.

        Behavior:
            - All registered hooks are executed.
            - No exception ever propagates.
            - All hooks are executed even if one fails.
        """
        for hook in self._hooks:
            with suppress(Exception):
                hook(amount)

    # --------------------------------------------------------------------------
    # Hook registration
    # --------------------------------------------------------------------------
    def bind_increment_hook(self, fn: Callable[[int], None]) -> None:
        """
        Register a callback to be executed on each increment.

        This is the official expansion point for any upper layer.

        Hooks MUST:
            - never raise (exceptions suppressed),
            - be pure side effects (no return),
            - not assume call order or exclusivity.

        Notes:
            - Hooks are executed in registration order.
        """
        self._hooks.append(fn)


# ╭────────────────────────────────────────────────────────────────────────────╮
# │Internal C0 registry (process lifetime)                                     │
# ╰────────────────────────────────────────────────────────────────────────────╯
_internal_metrics: dict[str, Counter] = {}


# ╭────────────────────────────────────────────────────────────────────────────╮
# │Internal C0 registry (process lifetime)                                     │
# ╰────────────────────────────────────────────────────────────────────────────╯
def define_counter(name: str) -> Counter:
    """
    Create or retrieve a C0 counter (idempotent).
    """
    with _METRICS_LOCK:
        existing = _internal_metrics.get(name)
        if existing is not None:
            return existing

        cnt = Counter(name)
        _internal_metrics[name] = cnt
        return cnt


def get_internal_counter(name: str) -> Counter | None:
    """Return the C0 counter if it exists, else None."""
    return _internal_metrics.get(name)


def list_internal_counters() -> Iterable[str]:
    """Return an iterable of all defined internal counter names."""
    return _internal_metrics.keys()
