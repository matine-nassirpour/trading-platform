from typing import ClassVar

from quantum.domain.shared.primitives.closed_set_value_object import (
    ClosedSetValueObject,
)


class TimeInForce(ClosedSetValueObject):
    _ALLOWED_VALUES: ClassVar[frozenset[str]] = frozenset(
        {
            "gtc",
            "day",
            "specified",
            "specified_day",
        }
    )
