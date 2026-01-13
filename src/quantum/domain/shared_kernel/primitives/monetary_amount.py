from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal

from quantum.domain.shared_kernel.architecture.immutable_dataclass import (
    immutable_dataclass,
)
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.mutation_key import MutationKey
from quantum.domain.shared_kernel.primitives.numeric_value_object import (
    NumericValueObject,
)
from quantum.domain.shared_kernel.value_objects.currency import Currency


@immutable_dataclass
class MonetaryAmount(NumericValueObject, ABC):
    """
    Abstract base class for all monetary quantities.

    HARD GUARANTEES:
    - Currency-aware
    - Decimal-only
    - Fully capability-immutable
    - Cannot be instantiated directly
    """

    value: Decimal
    currency: Currency

    @abstractmethod
    def _monetary_kind(self) -> None:
        """
        Architectural tag.

        This method has no runtime meaning.
        It exists solely to make MonetaryAmount abstract.
        """
        raise NotImplementedError

    def _validate_semantics(self, key: MutationKey) -> None:
        if not isinstance(self.currency, Currency):
            raise InvariantViolation(
                f"{self.__class__.__name__} requires a valid Currency"
            )
