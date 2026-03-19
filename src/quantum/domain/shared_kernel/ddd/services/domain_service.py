import inspect

from abc import ABC, ABCMeta
from typing import Any, final


@final
class _DomainServiceMeta(ABCMeta):
    """
    Metaclass enforcing strict Domain Service constraints.

    Guarantees:
    - cannot define instance state
    - cannot define __init__
    - cannot be instantiated
    - must only expose staticmethods or classmethods as public behavior
    """

    def __new__(
        mcls,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
    ) -> type:
        cls = super().__new__(mcls, name, bases, namespace)

        if name == "DomainService":
            return cls

        # Forbid instance constructor on concrete subclasses
        if "__init__" in namespace:
            raise TypeError(
                f"{name} must not define __init__. Domain Services are stateless."
            )

        # Forbid declared instance/class state on the service itself
        annotations = namespace.get("__annotations__", {})
        if annotations:
            raise TypeError(
                f"{name} must not define attributes. Domain Services are stateless."
            )

        # Forbid public instance methods
        for attr_name, attr_value in namespace.items():
            if attr_name.startswith("_"):
                continue

            if not callable(attr_value):
                continue

            descriptor = inspect.getattr_static(cls, attr_name)

            if not isinstance(descriptor, (staticmethod, classmethod)):
                raise TypeError(
                    f"{name}.{attr_name} must be a staticmethod or classmethod."
                )

        return cls

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        raise TypeError(
            f"{cls.__name__} cannot be instantiated. Domain Services are stateless."
        )


class DomainService(ABC, metaclass=_DomainServiceMeta):
    """
    Marker base class for Domain Services.

    Domain Services represent domain logic that:
    - does not naturally belong to an Entity or Value Object
    - is stateless
    - is pure
    - is deterministic
    - has no side-effects
    """

    __slots__ = ()
