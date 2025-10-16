"""
Quantum Timeout Utilities
──────────────────────────────────────────────────────────────────────────────
Provides cross-platform, testable timeout enforcement for both sync and async
functions. Designed for integration in `resilient_call` and other reliability
wrappers.

Key features:
- True timeout enforcement for sync and async callables
- Cross-platform (no signal/alarm)
- Thread-safe and reusable
- Consistent TimeoutError semantics
- Non-blocking design suitable for production use
"""

from __future__ import annotations

import asyncio
import concurrent.futures
from collections.abc import Callable, Generator
from contextlib import contextmanager
from typing import Any, TypeVar

T = TypeVar("T")

# Shared thread pool to amortize thread creation
_EXECUTOR = concurrent.futures.ThreadPoolExecutor(
    max_workers=8,
    thread_name_prefix="quantum-timeout",
)


# ──────────────────────────────────────────────────────────────────────────────
# SYNC TIMEOUT (Thread-based)
# ──────────────────────────────────────────────────────────────────────────────


def run_with_timeout_sync(
    func: Callable[..., T], *args, timeout_sec: float, call_name: str, **kwargs
) -> T:
    """
    Runs a blocking function with a timeout using a thread executor.
    Raises TimeoutError if limit is exceeded.
    """
    future = _EXECUTOR.submit(func, *args, **kwargs)
    try:
        return future.result(timeout=timeout_sec)
    except concurrent.futures.TimeoutError:
        future.cancel()
        raise TimeoutError(f"[{call_name}] execution exceeded {timeout_sec:.2f}s")


# ──────────────────────────────────────────────────────────────────────────────
# ASYNC TIMEOUT
# ──────────────────────────────────────────────────────────────────────────────


async def run_with_timeout_async(
    func: Callable[..., Any],
    *args,
    timeout_sec: float,
    call_name: str,
    **kwargs,
) -> Any:
    """
    Runs an async function with timeout enforcement via asyncio.wait_for.
    Raises TimeoutError consistently.
    """
    try:
        return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout_sec)
    except TimeoutError:
        raise TimeoutError(f"[{call_name}] async execution exceeded {timeout_sec:.2f}s")


# ──────────────────────────────────────────────────────────────────────────────
# Context Manager (diagnostic only, non-enforcing)
# ──────────────────────────────────────────────────────────────────────────────


@contextmanager
def diagnostic_timer(call_name: str) -> Generator[None]:
    """
    Context manager that records elapsed time for diagnostics/logging.
    Does not enforce timeout, only measures duration.
    """
    import time

    start = time.time()
    try:
        yield
    finally:
        elapsed = time.time() - start
        if elapsed > 5.0:  # threshold for long-running ops
            import logging

            logger = logging.getLogger("quantum.timeout")
            logger.warning(
                f"[{call_name}] operation took {elapsed:.2f}s (>5s)",
                extra={"attrs": {"duration_s": elapsed}},
            )
