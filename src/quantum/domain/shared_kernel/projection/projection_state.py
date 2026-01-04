from abc import ABC
from dataclasses import dataclass

from quantum.domain.shared_kernel.primitives.value_object import ValueObject


@dataclass(frozen=True)
class ProjectionState(ValueObject, ABC):
    """
    Base class for all derived (projected) states.

    Properties:
    - Immutable
    - Fully derived from domain events
    - Reconstructible at any time
    """

    # No fields here on purpose
    # Concrete projections define their own state
    pass
