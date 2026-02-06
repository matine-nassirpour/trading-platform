from abc import abstractmethod
from typing import Protocol, runtime_checkable

from quantum.domain.shared_kernel.money.daily_loss import DailyLoss
from quantum.domain.shared_kernel.money.drawdown import Drawdown
from quantum.domain.shared_kernel.money.equity import Equity
from quantum.domain.shared_kernel.money.notional import Notional
from quantum.domain.shared_kernel.money.risk_exposure import RiskExposure


@runtime_checkable
class FinancialStateProvider(Protocol):
    """
    Application port giving access to current financial metrics.
    """

    @abstractmethod
    def current_drawdown(self) -> Drawdown:
        raise NotImplementedError

    @abstractmethod
    def current_daily_loss(self) -> DailyLoss:
        raise NotImplementedError

    @abstractmethod
    def current_notional(self) -> Notional:
        raise NotImplementedError

    @abstractmethod
    def current_exposure(self) -> RiskExposure:
        raise NotImplementedError

    @abstractmethod
    def current_equity(self) -> Equity:
        raise NotImplementedError
