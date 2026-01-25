from abc import ABC

from quantum.domain.shared_kernel.primitives._validated_frozen_dataclass import (
    _ValidatedFrozenDataclass,
)


class ValueObject(_ValidatedFrozenDataclass, ABC):
    """
    Canonical base class for all Value Objects.
    """

    __slots__ = ()
