from typing import ClassVar

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.primitives.closed_set_value_object import (
    ClosedSetValueObject,
)


class OrderCheckOutcome(ClosedSetValueObject):
    """
    Outcome of pre-execution order checks.
    """

    _ALLOWED_VALUES: ClassVar[frozenset[str]] = frozenset(
        {
            "accepted",
            "insufficient_margin",
            "invalid_price",
            "invalid_volume",
            "market_closed",
            "unknown_error",
        }
    )

    def _closed_set_type(self) -> None:
        pass

    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.VALUE_OBJECT
