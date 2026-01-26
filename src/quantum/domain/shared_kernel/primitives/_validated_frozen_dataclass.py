from abc import ABC, abstractmethod

from quantum.domain.shared_kernel.primitives.structural_contract import (
    _validate_structural_contract,
)


class _ValidatedFrozenDataclass(ABC):
    """
    Internal base class for all domain primitives requiring:

    - frozen dataclass
    - slots
    - deterministic construction
    - non-bypassable validation
    - zero mutation
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
                f"Use _validate() instead."
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

    def _run_validation(self) -> None:
        """
        Non-overridable validation entrypoint.
        """
        self._validate()

    def __post_init__(self) -> None:
        """
        FINAL — must never be overridden.
        """

        # Enforce structural contract ONCE
        _validate_structural_contract(type(self))

        self._run_validation()
