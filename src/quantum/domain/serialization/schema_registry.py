from __future__ import annotations

import logging
import threading

from typing import Any, TypeVar, final

logger = logging.getLogger(__name__)

T = TypeVar("T")


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Thread-safe registry for event schemas                                     │
# ╰────────────────────────────────────────────────────────────────────────────╯
@final
class EventSchemaRegistry:
    """
    Thread-safe, immutable-on-read registry for event classes.

    This ensures safe concurrent access when multiple modules
    register events during runtime initialization.

    Implements:
      - Write access protected by RLock
      - Snapshot immutability for readers
      - Introspectable schema map
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._registry: dict[str, type[Any]] = {}

    # ─── Registration
    def register(self, event_cls: type[Any]) -> type[Any]:
        """Registers a new event class in a thread-safe manner."""
        name = getattr(event_cls, "event_name", None)
        version = getattr(event_cls, "schema_version", None)

        if not name:
            raise ValueError(f"Event class {event_cls.__name__} missing 'event_name'")
        if not isinstance(version, int):
            raise ValueError(
                f"Event class {event_cls.__name__} missing valid schema_version"
            )

        key = f"{name}.v{version}"

        with self._lock:
            if key in self._registry:
                existing = self._registry[key]
                if existing is not event_cls:
                    logger.warning(
                        f"Schema registry conflict for key '{key}': "
                        f"{existing.__name__} already registered, ignoring duplicate {event_cls.__name__}"
                    )
                    return existing
            self._registry[key] = event_cls
            logger.debug(f"Registered event schema: {key}")
            return event_cls

    # ─── Lookup
    def get(self, key: str) -> type[Any] | None:
        """Thread-safe lookup of an event schema by key."""
        with self._lock:
            return self._registry.get(key)

    def get_all(self) -> dict[str, type[Any]]:
        """Returns a snapshot copy of all registered event schemas."""
        with self._lock:
            return dict(self._registry)

    # ─── Introspection
    def __contains__(self, key: str) -> bool:
        with self._lock:
            return key in self._registry

    def __len__(self) -> int:
        with self._lock:
            return len(self._registry)

    def __repr__(self) -> str:
        with self._lock:
            keys = ", ".join(sorted(self._registry.keys()))
            return f"<EventSchemaRegistry keys=[{keys}]>"


# ─── Global instance (safe singleton)
REGISTRY = EventSchemaRegistry()


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Decorator API                                                              │
# ╰────────────────────────────────────────────────────────────────────────────╯
def register_event(cls: type[T]) -> type[T]:
    """
    Decorator used to register an event class.
    """
    REGISTRY.register(cls)
    return cls


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Helper functions for lookup                                                │
# ╰────────────────────────────────────────────────────────────────────────────╯
def resolve_event_schema(event_name: str, version: int = 1) -> type[Any] | None:
    """Resolves an event schema by name and version."""
    key = f"{event_name}.v{version}"
    return REGISTRY.get(key)


def list_registered_events() -> list[str]:
    """Returns the list of registered event keys."""
    return sorted(REGISTRY.get_all().keys())
