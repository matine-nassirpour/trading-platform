"""
Streamlit Inputs: Adapt UI actions to use cases (Application).
Do not import domain/infra here.
"""

from typing import Protocol


class RefreshMarketUseCase(Protocol):
    def execute(self, *, symbol: str | None = None) -> None: ...


class GetPositionsQuery(Protocol):
    def execute(self) -> list[dict]: ...


def on_refresh(use_case: RefreshMarketUseCase, *, symbol: str | None = None) -> None:
    use_case.execute(symbol=symbol)


def get_positions(query: GetPositionsQuery) -> list[dict]:
    return query.execute()
