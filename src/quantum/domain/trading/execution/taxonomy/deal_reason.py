from typing import ClassVar

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.primitives.closed_set_value_object import (
    ClosedSetValueObject,
)


class DealReason(ClosedSetValueObject):
    """
    Reason for deal execution.
    """

    _ALLOWED_VALUES: ClassVar[frozenset[str]] = frozenset(
        {
            "client",  # user / algo
            "mobile",
            "web",
            "sl",
            "tp",
            "so",
            "rollover",  # swap/rollover
            "reverse",  # reverse position
        }
    )

    def _closed_set_type(self) -> None:
        pass

    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.VALUE_OBJECT
