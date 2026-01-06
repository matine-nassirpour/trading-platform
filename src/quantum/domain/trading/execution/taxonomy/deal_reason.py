from typing import ClassVar

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
