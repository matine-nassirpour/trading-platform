from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared_kernel.primitives.closed_set_value_object import (
    ClosedSetValueObject,
)


@dataclass(frozen=True, slots=True)
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
