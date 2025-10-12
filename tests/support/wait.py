from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def wait_until(
    predicate: Callable[[], bool],
    *,
    timeout_s: float = 2.0,
    poll_s: float = 0.05,
) -> bool:
    """
    Poll a predicate until it returns True or timeout elapses.
    Returns True on success, False on timeout.
    """
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(poll_s)
    return False
