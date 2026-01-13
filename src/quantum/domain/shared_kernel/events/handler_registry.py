from __future__ import annotations

from collections.abc import Callable, Mapping
from types import MappingProxyType

from quantum.domain.shared_kernel.events.base_event import BaseEvent

EventKey = tuple[str, int]
EventHandler = Callable[[object, BaseEvent], None]


def build_handler_registry(cls: type) -> Mapping[EventKey, EventHandler]:
    handlers: dict[EventKey, EventHandler] = {}

    for base in reversed(cls.__mro__):
        for attr in base.__dict__.values():
            key = getattr(attr, "__event_key__", None)
            if key is None:
                continue

            if key in handlers:
                raise TypeError(f"Duplicate event handler for {key} in {cls.__name__}")

            handlers[key] = attr

    # Freeze the mapping: immutable, audit-grade
    return MappingProxyType(handlers)
