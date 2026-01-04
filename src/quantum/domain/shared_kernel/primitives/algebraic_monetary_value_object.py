from __future__ import annotations

from abc import ABC, abstractmethod

from quantum.domain.shared_kernel.errors.invariants import CurrencyMismatch
from quantum.domain.shared_kernel.primitives.monetary_amount import MonetaryAmount


class AlgebraicMonetaryValueObject(MonetaryAmount, ABC):
    """
    Monetary amount that is explicitly algebraically composable.
    """

    def _check_currency(self, other: MonetaryAmount) -> None:
        if self.currency != other.currency:
            raise CurrencyMismatch(
                f"Currency mismatch: {self.currency} vs {other.currency}"
            )

    @abstractmethod
    def add(self, other: MonetaryAmount) -> MonetaryAmount:
        raise NotImplementedError

    @abstractmethod
    def subtract(self, other: MonetaryAmount) -> MonetaryAmount:
        raise NotImplementedError
