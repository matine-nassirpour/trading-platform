from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class BuildInfoProvider(Protocol):
    """
    Abstraction for refreshing build metadata from environment variables.

    This avoids any dependency on implementation details like
    refresh_build_info_from_env(), keeping LifecycleService agnostic.
    """

    def refresh(self) -> None:
        """Refresh build metadata."""
        ...
