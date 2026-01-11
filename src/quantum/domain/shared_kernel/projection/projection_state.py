from abc import ABC
from dataclasses import dataclass

from quantum.domain.shared_kernel.architecture.read_model import ReadModel


@dataclass(frozen=True)
class ProjectionState(ReadModel, ABC):
    """
    Base class for all derived (projected) read-side states.

    Guarantees:
    - Immutable
    - Fully derived from domain events
    - Reconstructible by replay
    - Contains NO domain logic
    """

    pass
