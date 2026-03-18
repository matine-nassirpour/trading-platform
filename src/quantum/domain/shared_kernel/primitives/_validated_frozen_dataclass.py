from abc import ABC, abstractmethod

from quantum.domain.shared_kernel.primitives.structural_contract import (
    _assert_deep_immutability_of_instance_fields,
    _validate_structural_contract,
)


class _ValidatedFrozenDataclass(ABC):
    """
    Internal base class for domain primitives requiring:

    - frozen dataclass
    - slots-only instance layout
    - deterministic construction
    - final validation entrypoint
    - deep immutability of fields at construction time

    IMPORTANT:
    This contract guarantees domain-safe deep immutability by construction.
    It does not claim that Python objects are impossible to subvert by hostile
    reflection or deliberate low-level bypass.
    """

    __slots__ = ()

    # --- Class creation enforcement -------------------------------------------

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        # Skip base class itself
        if cls is _ValidatedFrozenDataclass:
            return

        # Forbid override of __post_init__
        if "__post_init__" in cls.__dict__:
            raise TypeError(
                f"{cls.__name__} must NOT override __post_init__. "
                "Use _validate() instead."
            )

    # --- Mandatory domain contract --------------------------------------------

    @abstractmethod
    def _validate(self) -> None:
        """
        Enforces all invariants.

        Must raise DomainError / InvariantViolation on failure.
        """
        raise NotImplementedError

    # --- Construction Guarantee -----------------------------------------------

    def __post_init__(self) -> None:
        """
        Must never be overridden.
        """

        _validate_structural_contract(type(self))
        _assert_deep_immutability_of_instance_fields(self)
        self._validate()
