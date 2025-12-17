from typing import Protocol

from runtime.lifecycle.state_machine import RuntimeState


class RuntimeStatePort(Protocol):
    """
    Minimal read-only port exposing the runtime lifecycle state.

    This port exists to avoid coupling adapters (HTTP, CLI, etc.)
    to the concrete RuntimeLifecycleEngine implementation.
    """

    @property
    def state(self) -> RuntimeState: ...
