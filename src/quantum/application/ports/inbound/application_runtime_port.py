from typing import Protocol


class ApplicationRuntimePort(Protocol):
    """
    Inbound port exposed by the Application layer to the Runtime.

    Contract:
    - Controls application lifecycle only.
    - No infrastructure concerns.
    - No domain logic leakage.
    """

    async def start(self) -> None:
        """
        Start the application layer.
        Must be idempotent or fail-fast.
        """
        ...

    async def stop(self) -> None:
        """
        Stop the application layer.
        Must be safe to call during partial startup.
        """
        ...
