from typing import ClassVar

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.primitives.closed_set_value_object import (
    ClosedSetValueObject,
)


class KillSwitchReason(ClosedSetValueObject):
    """
    Canonical kill switch trigger reason.
    """

    _ALLOWED_VALUES: ClassVar[frozenset[str]] = frozenset(
        {
            "risk_limit",
            "network",
            "broker_rejects",
            "manual",
        }
    )

    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.VALUE_OBJECT
