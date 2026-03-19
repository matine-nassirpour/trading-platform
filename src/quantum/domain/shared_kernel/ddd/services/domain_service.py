from abc import ABC, ABCMeta
from typing import Any, Final, final

_FORBIDDEN_LIFECYCLE_NAMES: Final[frozenset[str]] = frozenset(
    {
        "__init__",
        "__new__",
        "__setattr__",
        "__delattr__",
    }
)


def _validate_domain_service_definition(cls: type) -> None:
    """
    Validates the architectural contract of a Domain Service.

    DESIGN INTENT:
    A Domain Service is a stateless semantic host for domain logic that does not
    naturally belong to an Entity or Value Object.

    This validator is intentionally LIGHTWEIGHT and PROPORTIONATE:
    - it enforces the important architectural constraints;
    - it avoids brittle namespace policing;
    - it does not confuse Python syntax choices with architectural violations.

    ENFORCED RULES:
    - DomainService subclasses must remain non-instantiable;
    - DomainService subclasses must not define lifecycle / mutation hooks;
    - DomainService subclasses must not define instance storage;
    - abstract subclasses are allowed.

    NON-GOALS:
    - policing every namespace symbol;
    - forbidding benign annotations;
    - forbidding private constants or helper metadata;
    - forcing every public method to be static/classmethod via metaprogramming.
    """

    if cls is DomainService:
        return

    namespace = cls.__dict__

    forbidden = _FORBIDDEN_LIFECYCLE_NAMES.intersection(namespace.keys())
    if forbidden:
        names = ", ".join(sorted(forbidden))
        raise TypeError(
            f"{cls.__name__} must not define {names}. "
            "Domain Services are stateless semantic types and must not own "
            "instance lifecycle or mutation hooks."
        )

    slots = namespace.get("__slots__", ())
    if slots != ():
        raise TypeError(
            f"{cls.__name__} must declare '__slots__ = ()' or inherit it unchanged. "
            "Domain Services must not expose instance storage."
        )

    # Defensive runtime sanity check:
    # if raw allocation succeeds and an instance dictionary appears,
    # the type violates the no-instance-storage contract.
    try:
        dummy = object.__new__(cls)
    except Exception:
        return

    if hasattr(dummy, "__dict__"):
        raise TypeError(
            f"{cls.__name__} exposes instance __dict__, which is forbidden for "
            "Domain Services."
        )


@final
class _DomainServiceMeta(ABCMeta):
    """
    Metaclass enforcing the minimal, durable Domain Service contract.

    HARD GUARANTEES:
    - Domain Services cannot be instantiated;
    - Domain Services cannot define instance lifecycle hooks;
    - Domain Services cannot expose instance storage.

    IMPORTANT:
    This metaclass intentionally does NOT police every symbol declared in the
    class body. Excessive namespace policing is brittle, high-friction, and
    architecturally noisy.

    The goal is to enforce what matters, not to turn the shared kernel into a
    syntax tribunal.
    """

    def __new__(
        mcls,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
    ) -> type:
        cls = super().__new__(mcls, name, bases, namespace)
        _validate_domain_service_definition(cls)
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
    - should remain deterministic and side-effect free from the domain
      perspective.

    ENGINEERING RULES:
    - prefer @staticmethod for pure operations;
    - use @classmethod only when behavior is genuinely type-relative;
    - do not introduce hidden caches, registries, or mutable class state;
    - do not access infrastructure from here;
    - do not use this type as a disguised application service.

    NOTE:
    Architectural purity is enforced primarily by placement, dependency
    direction, and code review discipline. This base enforces only the minimal
    structural guarantees that are robustly checkable at runtime.
    """

    __slots__ = ()
