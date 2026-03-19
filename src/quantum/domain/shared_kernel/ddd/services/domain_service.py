import inspect

from abc import ABC, ABCMeta
from types import FunctionType
from typing import Any, Final, final

_ALLOWED_CLASS_NAMESPACE_NAMES: Final[frozenset[str]] = frozenset(
    {
        "__module__",
        "__qualname__",
        "__doc__",
        "__slots__",
        "__static_attributes__",
        "__firstlineno__",
        "__annotations__",
        "__abstractmethods__",
    }
)

_FORBIDDEN_SPECIAL_NAMES: Final[frozenset[str]] = frozenset(
    {
        "__init__",
        "__new__",
        "__setattr__",
        "__delattr__",
    }
)


def _is_allowed_public_descriptor(descriptor: Any) -> bool:
    """
    Returns True only for explicitly allowed public behavior descriptors.

    Allowed public callable forms:
    - @staticmethod
    - @classmethod

    Explicitly forbidden:
    - plain instance methods
    - property
    - arbitrary descriptors
    """
    return isinstance(descriptor, (staticmethod, classmethod))


def _is_internal_abc_helper(name: str, value: Any) -> bool:
    """
    Allows ABC internals synthesized by the runtime.

    In practice, abstract methods appear as regular function objects in the
    namespace during class creation. They must not be mistaken for class state.
    """
    return getattr(value, "__isabstractmethod__", False)


def _is_plain_function(value: Any) -> bool:
    """
    True for function objects defined in the class body before descriptor binding.
    """
    return isinstance(value, FunctionType)


def _validate_forbidden_special_names(*, cls: type, namespace: dict[str, Any]) -> None:
    forbidden_specials = _FORBIDDEN_SPECIAL_NAMES.intersection(namespace.keys())
    if not forbidden_specials:
        return

    names = ", ".join(sorted(forbidden_specials))
    raise TypeError(
        f"{cls.__name__} must not define {names}. "
        "Domain Services are non-instantiable and stateless."
    )


def _validate_no_annotations(*, cls: type, namespace: dict[str, Any]) -> None:
    annotations = namespace.get("__annotations__", {})
    if not annotations:
        return

    declared = ", ".join(sorted(annotations))
    raise TypeError(
        f"{cls.__name__} must not declare attributes ({declared}). "
        "Domain Services are stateless and must not carry class state."
    )


def _validate_slots_discipline(*, cls: type, namespace: dict[str, Any]) -> None:
    if "__slots__" not in namespace:
        return

    if namespace["__slots__"] == ():
        return

    raise TypeError(
        f"{cls.__name__} must declare '__slots__ = ()' or omit __slots__. "
        "Domain Services must not expose instance storage."
    )


def _validate_domain_service_namespace(
    *,
    cls: type,
    namespace: dict[str, Any],
) -> None:
    """
    Validates the full class namespace of a Domain Service subclass.

    POLICY:
    Everything is forbidden unless explicitly allowed.

    Allowed entries:
    - structural metadata injected by Python;
    - __slots__ = ();
    - abstract methods helpers;
    - private/protected helper methods as plain functions;
    - public methods only if declared as @staticmethod or @classmethod.

    Forbidden entries:
    - any class attribute carrying state;
    - any property;
    - any custom descriptor;
    - any public plain function (instance method);
    - any special hook enabling instance mutation or lifecycle control.
    """
    # --- 1. Explicitly forbid lifecycle / mutation hooks
    _validate_forbidden_special_names(cls=cls, namespace=namespace)

    # --- 2. Annotations are forbidden as state declarations
    _validate_no_annotations(cls=cls, namespace=namespace)

    # --- 3. __slots__ discipline
    _validate_slots_discipline(cls=cls, namespace=namespace)

    # --- 4. Validate every class namespace entry
    for attr_name, attr_value in namespace.items():
        if attr_name in _ALLOWED_CLASS_NAMESPACE_NAMES:
            continue

        # Public API
        if not attr_name.startswith("_"):
            descriptor = inspect.getattr_static(cls, attr_name)

            if not _is_allowed_public_descriptor(descriptor):
                raise TypeError(
                    f"{cls.__name__}.{attr_name} must be declared as "
                    "@staticmethod or @classmethod. Public instance methods, "
                    "properties, descriptors, and class attributes are forbidden "
                    "on Domain Services."
                )

            continue

        # Private / protected entries ------------------------------------------
        # Private/protected helper methods are allowed only as plain functions
        # (which will become bound methods if ever accessed on an instance,
        # but instances are impossible by construction).
        if _is_plain_function(attr_value) or _is_internal_abc_helper(
            attr_name, attr_value
        ):
            continue

        # Allow private/protected staticmethod/classmethod helpers as well.
        if isinstance(attr_value, (staticmethod, classmethod)):
            continue

        raise TypeError(
            f"{cls.__name__}.{attr_name} is forbidden. "
            "Domain Services must not declare private or protected state, "
            "descriptors, caches, registries, constants, or any other class-level "
            "data. Only helper methods are allowed."
        )


@final
class _DomainServiceMeta(ABCMeta):
    """
    Metaclass enforcing a truly stateless Domain Service contract.

    HARD GUARANTEES:
    - a Domain Service cannot be instantiated;
    - a Domain Service cannot define instance state;
    - a Domain Service cannot define class state;
    - a Domain Service cannot define __init__ / __new__;
    - a Domain Service may expose only @staticmethod or @classmethod as
      public behavior;
    - no arbitrary descriptor or property is allowed;
    - no hidden mutable cache, registry, constant bag, or side-channel state
      may be declared in the class namespace.

    ARCHITECTURAL INTENT:
    A Domain Service is a pure semantic host for domain logic that does not
    belong naturally to an Entity or Value Object. It is not an object with
    lifecycle or memory.
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

        _validate_domain_service_namespace(cls=cls, namespace=namespace)
        return cls

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        raise TypeError(
            f"{cls.__name__} cannot be instantiated. "
            "Domain Services are stateless semantic types."
        )


class DomainService(ABC, metaclass=_DomainServiceMeta):
    """
    Marker base class for pure, stateless Domain Services.

    A Domain Service:
    - hosts domain logic that does not naturally belong to an Entity or
      Value Object;
    - is stateless by construction;
    - is non-instantiable by construction;
    - must remain pure and deterministic.

    USAGE RULE:
    Expose public behavior only through @staticmethod or @classmethod.
    """

    __slots__ = ()
