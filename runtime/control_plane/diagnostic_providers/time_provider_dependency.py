from __future__ import annotations

from quantum.application.ports.outbound.time_provider_port import TimeProviderPort


class TimeProviderDependency:
    """
    Small indirection layer for injecting TimeProviderPort into diagnostic providers.

    This keeps providers fully decoupled from the runtime engine while still
    respecting Clean Architecture + DIP.

    The Runtime system assigns the concrete TimeProviderPort during composition.
    """

    _provider: TimeProviderPort | None = None

    @classmethod
    def set(cls, provider: TimeProviderPort) -> None:
        cls._provider = provider

    @classmethod
    def get(cls) -> TimeProviderPort:
        if cls._provider is None:
            raise RuntimeError(
                "TimeProviderDependency not initialized — "
                "TimeProviderPort must be injected at runtime composition."
            )
        return cls._provider
