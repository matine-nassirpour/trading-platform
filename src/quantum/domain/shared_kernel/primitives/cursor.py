from abc import ABC
from dataclasses import dataclass

from quantum.domain.shared_kernel.primitives._validated_frozen_dataclass import (
    _ValidatedFrozenDataclass,
)


@dataclass(frozen=True, slots=True)
class Cursor(_ValidatedFrozenDataclass, ABC):
    """
    Monotonic, audit-grade cursor.

    A Cursor represents a strictly ordered position in a domain stream
    (e.g. event sequence, market feed, etc).
    """
