from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from quantum.domain.shared_kernel.projection.projection_cursor import ProjectionCursor

S = TypeVar("S")


class ProjectionRepositoryPort(ABC, Generic[S]):
    """
    Storage abstraction for projections.
    """

    @abstractmethod
    def load(self) -> tuple[S, ProjectionCursor]:
        raise NotImplementedError

    @abstractmethod
    def save(self, state: S, cursor: ProjectionCursor) -> None:
        raise NotImplementedError
