from typing import ClassVar

from quantum.domain.shared.primitives.closed_set_value_object import (
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
