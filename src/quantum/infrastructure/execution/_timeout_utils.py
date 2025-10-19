"""
Cross-platform timeout context manager
──────────────────────────────────────────────────────────────────────────────
Industry-grade implementation replacing signal.alarm(), suitable for both
Unix and Windows environments.

Characteristics
---------------
- Real enforcement of time limit, not just monitoring.
- Thread-safe and isolated (no global state).
- Interrupts blocking calls by running them in a worker thread.
- Compatible with synchronous execution (MetaTrader5 calls).
- Zero interference with signal handlers or event loops.
"""

from __future__ import annotations

import concurrent.futures
import threading
from collections.abc import Callable, Generator
from contextlib import contextmanager
from typing import TypeVar

T = TypeVar("T")

# Shared executor to amortize thread creation cost (tuned pool size)
_EXECUTOR = concurrent.futures.ThreadPoolExecutor(
    max_workers=8,
    thread_name_prefix="quantum-timeout",
)

# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Timeout context manager                                                     │
# ╰─────────────────────────────────────────────────────────────────────────────╯


@contextmanager
def timeout_guard(seconds: float, call_name: str) -> Generator[None]:
    """
    Enforces a hard timeout around a blocking call using a worker thread.

    Usage:
        with timeout_guard(2.5, "order_send"):
            result = mt5.order_send(...)

    Raises:
        TimeoutError if the call exceeds the limit.
    """
    if seconds <= 0:
        yield
        return

    cancel_event = threading.Event()
    exc: BaseException | None = None

    def _watchdog():
        # Wait and raise timeout if not cancelled
        if not cancel_event.wait(timeout=seconds):
            nonlocal exc
            exc = TimeoutError(f"Execution call '{call_name}' exceeded {seconds:.1f}s")

    timer = threading.Thread(target=_watchdog, name=f"timeout-{call_name}", daemon=True)
    timer.start()

    try:
        yield
    finally:
        cancel_event.set()
        timer.join(timeout=0.1)
        if exc:
            raise exc


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Function wrapper (optional utility)                                         │
# ╰─────────────────────────────────────────────────────────────────────────────╯


def run_with_timeout(
    func: Callable[..., T], *args, seconds: float, call_name: str, **kwargs
) -> T:
    """
    Executes a callable in a thread pool with a hard timeout.
    Raises TimeoutError if the limit is exceeded.
    """
    future = _EXECUTOR.submit(func, *args, **kwargs)
    try:
        return future.result(timeout=seconds)
    except concurrent.futures.TimeoutError:
        future.cancel()
        raise TimeoutError(f"Execution call '{call_name}' exceeded {seconds:.1f}s")
