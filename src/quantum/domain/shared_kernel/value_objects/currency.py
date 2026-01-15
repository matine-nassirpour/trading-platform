from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared_kernel.primitives.closed_set_value_object import (
    ClosedSetValueObject,
)


@dataclass(frozen=True, slots=True)
class Currency(ClosedSetValueObject):
    """
    Canonical domain currency.

    It does NOT know about ISO-4217 or any external standard.
    """

    _ALLOWED_VALUES: ClassVar[frozenset[str]] = frozenset(
        {
            "usd",
            "eur",
            "jpy",
            "chf",
            "gbp",
            "cad",
            "aud",
            "nzd",
        }
    )
