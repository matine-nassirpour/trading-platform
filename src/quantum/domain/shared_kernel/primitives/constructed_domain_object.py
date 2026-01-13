from typing import Any

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation


class ConstructedDomainObject:
    """
    Atomic construction guard.

    Guarantees:
    - Object is unusable until fully validated
    - Invalid objects can never be observed or used
    """

    __slots__ = ("_constructed",)

    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls)
        object.__setattr__(obj, "_constructed", False)
        return obj

    def _mark_constructed(self) -> None:
        object.__setattr__(self, "_constructed", True)

    def _assert_constructed(self) -> None:
        if not object.__getattribute__(self, "_constructed"):
            raise InvariantViolation(
                f"{self.__class__.__name__} is not fully constructed and cannot be used"
            )

    def __getattribute__(self, name: str) -> Any:
        if name.startswith("_"):
            return object.__getattribute__(self, name)

        if not object.__getattribute__(self, "_constructed"):
            raise InvariantViolation(
                f"{self.__class__.__name__} is not fully constructed"
            )

        return object.__getattribute__(self, name)
