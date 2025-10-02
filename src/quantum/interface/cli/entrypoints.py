"""
CLI entries: Adapt commands/shells to use cases (Application).
Do not import domain/infra here.
"""

from typing import Protocol


class RefreshMarketUseCase(Protocol):
    def execute(self, *, symbol: str | None = None) -> None: ...


class ReconcileUseCase(Protocol):
    def execute(self) -> None: ...


def refresh_market(
    use_case: RefreshMarketUseCase, *, symbol: str | None = None
) -> None:
    use_case.execute(symbol=symbol)


def reconcile(use_case: ReconcileUseCase) -> None:
    use_case.execute()
