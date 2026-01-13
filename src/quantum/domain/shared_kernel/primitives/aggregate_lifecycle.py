from abc import ABC, abstractmethod


class AggregateLifecycle(ABC):
    """
    Formal lifecycle for all Event-Sourced Aggregates.

    Guarantees:
    - __init__ is never called during rehydration
    - only one canonical empty constructor exists
    """

    __slots__ = ()

    @abstractmethod
    def _lifecycle_anchor(self) -> None:
        """
        Architectural anchor.

        This method has no runtime semantics.
        It exists to make AggregateLifecycle a true abstract base class,
        enforcing that all concrete aggregates participate in the
        controlled lifecycle protocol.
        """
        raise NotImplementedError

    @classmethod
    def _empty(cls):
        """
        Constructs an uninitialized aggregate instance
        without calling __init__.
        """
        return object.__new__(cls)
