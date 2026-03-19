import inspect

from abc import ABC
from typing import final


@final
class _DomainServiceMeta(type):
    """
    Metaclass enforcing strict Domain Service constraints.

    Guarantees:

    - Cannot define instance state
    - Cannot define __init__
    - Cannot be instantiated
    - Must only expose staticmethods or classmethods
    - No side-effects allowed structurally
    """

    def __new__(mcls, name, bases, namespace):

        cls = super().__new__(mcls, name, bases, namespace)

        if name == "DomainService":
            return cls

        # Forbid instance constructor
        if "__init__" in namespace:
            raise TypeError(
                f"{name} must not define __init__. " f"Domain Services are stateless."
            )

        # Forbid instance attributes
        annotations = namespace.get("__annotations__", {})
        if annotations:
            raise TypeError(
                f"{name} must not define instance attributes. "
                f"Domain Services are stateless."
            )

        # Forbid non-static public methods
        for attr_name, attr_value in namespace.items():

            if attr_name.startswith("_"):
                continue

            if not callable(attr_value):
                continue

            descriptor = inspect.getattr_static(cls, attr_name)

            if not isinstance(descriptor, (staticmethod, classmethod)):
                raise TypeError(
                    f"{name}.{attr_name} must be staticmethod or classmethod"
                )

        return cls

    def __call__(cls, *args, **kwargs):
        raise TypeError(
            f"{cls.__name__} cannot be instantiated. " f"Domain Services are stateless."
        )


class DomainService(ABC, metaclass=_DomainServiceMeta):
    """
    Marker base class for Domain Services.

    Domain Services represent domain logic that:

    - Does not naturally belong to an Entity or Value Object
    - Is stateless
    - Is pure
    - Is deterministic
    - Has no side-effects

    Required for DDD correctness and certification discipline.
    """

    __slots__ = ()
