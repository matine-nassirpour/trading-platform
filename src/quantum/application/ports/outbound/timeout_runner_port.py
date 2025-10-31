from collections.abc import Awaitable, Callable
from typing import Any, Protocol, TypeVar

T = TypeVar("T")


class TimeoutRunnerPort(Protocol):
    """
    Abstract interface for timeout-enforced execution.

    This decouples the Application layer from any threading
    or asyncio infrastructure mechanisms.
    """

    def run_with_timeout_sync(
        self,
        func: Callable[..., T],
        *args: Any,
        timeout_sec: float,
        call_name: str,
        **kwargs: Any,
    ) -> T:
        """Execute a blocking callable with timeout enforcement."""
        ...

    async def run_with_timeout_async(
        self,
        func: Callable[..., Awaitable[T]],
        *args: Any,
        timeout_sec: float,
        call_name: str,
        **kwargs: Any,
    ) -> T:
        """Execute an asynchronous callable with timeout enforcement."""
        ...
