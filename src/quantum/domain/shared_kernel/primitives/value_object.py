from abc import ABC
from dataclasses import dataclass

from quantum.domain.shared_kernel.primitives._validated_frozen_dataclass import (
    _ValidatedFrozenDataclass,
)


@dataclass(frozen=True, slots=True)
class ValueObject(_ValidatedFrozenDataclass, ABC):
    """
    Canonical base class for all Value Objects.
    """
