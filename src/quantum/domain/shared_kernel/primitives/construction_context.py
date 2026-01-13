from __future__ import annotations

import contextvars

from contextlib import contextmanager

_IN_CONSTRUCTION: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "_IN_CONSTRUCTION", default=False
)


@contextmanager
def construction_window():
    token = _IN_CONSTRUCTION.set(True)
    try:
        yield
    finally:
        _IN_CONSTRUCTION.reset(token)


def is_in_construction() -> bool:
    return _IN_CONSTRUCTION.get()
