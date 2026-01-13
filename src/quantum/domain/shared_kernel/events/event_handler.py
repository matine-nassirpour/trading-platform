from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

F = TypeVar("F", bound=Callable)


def event_handler(event_name: str, event_version: int) -> Callable[[F], F]:
    """
    Declares a method as the canonical handler for a given domain event.

    This decorator does NOT register anything yet.
    It only annotates the function.
    """

    def decorator(func: F) -> F:
        func.__event_key__ = event_name, event_version
        return func

    return decorator
