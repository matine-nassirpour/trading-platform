from __future__ import annotations

import asyncio
import concurrent.futures
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from quantum.application.ports.outbound.timeout_runner_port import TimeoutRunnerPort

T = TypeVar("T")

_EXECUTOR = concurrent.futures.ThreadPoolExecutor(
    max_workers=8,
    thread_name_prefix="quantum-timeout",
)


class ThreadedTimeoutRunnerAdapter(TimeoutRunnerPort):
    """ThreadPool/asyncio-based implementation of TimeoutRunnerPort."""

    def run_with_timeout_sync(
        self,
        func: Callable[..., T],
        *args: Any,
        timeout_sec: float,
        call_name: str,
        **kwargs: Any,
    ) -> T:
        """Run a blocking function with a timeout using a thread executor."""
        future = _EXECUTOR.submit(func, *args, **kwargs)
        try:
            return future.result(timeout=timeout_sec)
        except concurrent.futures.TimeoutError:
            future.cancel()
            raise TimeoutError(f"[{call_name}] execution exceeded {timeout_sec:.2f}s")

    async def run_with_timeout_async(
        self,
        func: Callable[..., Awaitable[T]],
        *args: Any,
        timeout_sec: float,
        call_name: str,
        **kwargs: Any,
    ) -> T:
        """Run an async function with timeout enforcement via asyncio.wait_for."""
        try:
            return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout_sec)
        except TimeoutError:
            raise TimeoutError(
                f"[{call_name}] async execution exceeded {timeout_sec:.2f}s"
            )
