from typing import Protocol, runtime_checkable


@runtime_checkable
class LifecycleComponent(Protocol):
    """
    Technical lifecycle component managed by ApplicationOrchestrator.

    Contract:
    - No business workflow orchestration.
    - No domain decision logic.
    - start() must be idempotent or fail-fast.
    - stop() must be safe after partial startup.
    """

    @property
    def name(self) -> str: ...

    async def start(self) -> None: ...

    async def stop(self) -> None: ...
