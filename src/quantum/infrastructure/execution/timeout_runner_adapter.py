from __future__ import annotations

import asyncio
import concurrent.futures
import logging
import threading

from collections.abc import Awaitable, Callable
from contextlib import AbstractContextManager
from types import TracebackType
from typing import Any, Final, TypeVar

from quantum.application.ports.outbound.timeout_runner_port import TimeoutRunnerPort

LOGGER: Final = logging.getLogger(__name__)

T = TypeVar("T")


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Domain-level Exception Abstraction                                         │
# ╰────────────────────────────────────────────────────────────────────────────╯
class TimeoutExecutionError(TimeoutError):
    """
    Unified timeout abstraction for both sync and async executions.
    This prevents any mismatch between asyncio.TimeoutError and TimeoutError.
    """

    def __init__(self, operation: str, timeout_sec: float) -> None:
        super().__init__(f"[{operation}] execution exceeded {timeout_sec:.2f}s")
        self.operation = operation
        self.timeout_sec = timeout_sec


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Threaded/Async Timeout Runner Adapter                                      │
# ╰────────────────────────────────────────────────────────────────────────────╯
class ThreadedTimeoutRunnerAdapter(
    TimeoutRunnerPort,
    AbstractContextManager["ThreadedTimeoutRunnerAdapter"],
):
    """ThreadPool + asyncio-based implementation of TimeoutRunnerPort."""

    def __init__(
        self,
        *,
        max_workers: int = 8,
        thread_name_prefix: str = "quantum-timeout",
        logger: logging.Logger | None = None,
    ) -> None:
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix=thread_name_prefix,
        )
        self._logger = logger or LOGGER
        self._shutdown_lock = threading.Lock()
        self._is_shutdown = False

        self._logger.debug(
            "[TimeoutRunner] Initialized executor (max_workers=%d, prefix=%s)",
            max_workers,
            thread_name_prefix,
            extra={"attrs": {"max_workers": max_workers, "prefix": thread_name_prefix}},
        )

    # --------------------------------------------------------------------------
    # Sync Execution
    # --------------------------------------------------------------------------
    def run_with_timeout_sync(
        self,
        func: Callable[..., T],
        *args: Any,
        timeout_sec: float,
        call_name: str,
        **kwargs: Any,
    ) -> T:
        """Run a blocking function with timeout enforcement via threads."""
        if self._is_shutdown:
            raise RuntimeError("[TimeoutRunner] Executor already shut down")

        future = self._executor.submit(func, *args, **kwargs)
        try:
            return future.result(timeout=timeout_sec)
        except concurrent.futures.TimeoutError as exc:
            future.cancel()
            self._logger.warning(
                "[TimeoutRunner] %s exceeded %.2fs (sync)", call_name, timeout_sec
            )
            raise TimeoutExecutionError(call_name, timeout_sec) from exc
        except Exception:
            raise

    # --------------------------------------------------------------------------
    # Async Execution
    # --------------------------------------------------------------------------
    async def run_with_timeout_async(
        self,
        func: Callable[..., Awaitable[T]],
        *args: Any,
        timeout_sec: float,
        call_name: str,
        **kwargs: Any,
    ) -> T:
        """
        Run an async function with timeout enforcement via asyncio.wait_for.
        """
        if self._is_shutdown:
            raise RuntimeError("[TimeoutRunner] Executor already shut down")

        try:
            return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout_sec)
        except TimeoutError as exc:
            self._logger.warning(
                "[TimeoutRunner] %s exceeded %.2fs (async)", call_name, timeout_sec
            )
            raise TimeoutExecutionError(call_name, timeout_sec) from exc
        except Exception:
            raise

    # --------------------------------------------------------------------------
    # Lifecycle management
    # --------------------------------------------------------------------------
    def shutdown(self, wait: bool = True, cancel_futures: bool = True) -> None:
        """
        Gracefully shut down the executor.
        Should be called when the adapter is no longer needed (tests, app exit).
        """
        with self._shutdown_lock:
            if self._is_shutdown:
                return
            self._logger.debug(
                "[TimeoutRunner] Shutting down executor (wait=%s, cancel=%s)",
                wait,
                cancel_futures,
            )
            self._executor.shutdown(wait=wait, cancel_futures=cancel_futures)
            self._is_shutdown = True

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Allow usage as a context manager for deterministic cleanup."""
        self.shutdown(wait=True)
