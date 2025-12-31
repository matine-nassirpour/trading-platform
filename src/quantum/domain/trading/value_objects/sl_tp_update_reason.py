from typing import ClassVar

from quantum.domain.shared.primitives.closed_set_value_object import (
    ClosedSetValueObject,
)


class SlTpUpdateReason(ClosedSetValueObject):
    _ALLOWED_VALUES: ClassVar[frozenset[str]] = frozenset(
        {
            "manual",
            "rule",
            "risk",
        }
    )
