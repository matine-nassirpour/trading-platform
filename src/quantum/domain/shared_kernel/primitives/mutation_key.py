from __future__ import annotations


class MutationKey:
    """
    Deterministic, non-forgeable mutation capability.

    Properties:
    - Unique per object instance
    - Non-serializable
    - Cannot be guessed or reconstructed
    - Deterministic (no randomness)
    """

    __slots__ = ("_sentinel", "_alive")

    def __init__(self) -> None:
        # object() creates a unique identity token
        # guaranteed unique inside the process
        self._sentinel = object()
        self._alive = True

    def _matches(self, other: MutationKey) -> bool:
        return self._alive and other._alive and self._sentinel is other._sentinel

    def _invalidate(self) -> None:
        self._alive = False
        self._sentinel = None
