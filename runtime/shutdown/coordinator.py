from __future__ import annotations

import asyncio
import threading

from collections.abc import Callable, Coroutine
from typing import Any


class ShutdownCoordinator:
    """
    Deterministic, idempotent shutdown trigger.

    Responsibilities:
    - Ensure shutdown is requested exactly once.
    - Create at most one asyncio Task.
    - Be safe under signal storms.
    - Contain NO business logic.
    """

    def __init__(self, *, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        self._lock = threading.Lock()
        self._shutdown_requested = False
        self._task: asyncio.Task[None] | None = None

    def request(self, coro: Callable[[], Coroutine[Any, Any, None]]) -> None:
        """
        Request shutdown.

        This method is:
        - synchronous
        - signal-handler safe
        - idempotent
        """

        with self._lock:
            if self._shutdown_requested:
                return

            self._shutdown_requested = True

            # Schedule exactly one task on the loop
            self._task = self._loop.create_task(coro())
