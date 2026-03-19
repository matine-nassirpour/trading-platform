import inspect

from dataclasses import is_dataclass
from functools import cache

from quantum.domain.shared_kernel.foundation.contracts.violations import (
    StructuralContractViolation,
)


def _collect_all_slots(cls: type) -> set[str]:
    """
    Collects every declared slot across the full MRO.

    This is a representation-level concern only.
    It must not be mixed with deep-immutability or semantic domain policies.
    """
    slots: set[str] = set()

    for base in cls.__mro__:
        base_slots = getattr(base, "__slots__", None)
        if base_slots is None:
            continue

        if isinstance(base_slots, str):
            slots.add(base_slots)
        else:
            slots.update(base_slots)

    return slots


def _assert_instance_layout_is_dict_free(
    cls: type,
    *,
    forbid_instance_dict: bool,
) -> None:
    if not forbid_instance_dict:
        return

    try:
        dummy = object.__new__(cls)
    except Exception:
        # If the runtime cannot allocate a raw instance, class-level guarantees
        # are deemed sufficient.
        return

    if hasattr(dummy, "__dict__"):
        raise StructuralContractViolation(
            f"{cls.__name__} instances expose __dict__ despite slots. "
            "This is forbidden."
        )


@cache
def validate_python_dataclass_representation(
    cls: type,
    *,
    require_dataclass: bool = True,
    require_frozen: bool = True,
    require_slots: bool = True,
    forbid_instance_dict: bool = True,
    forbid_weakref: bool = True,
) -> None:
    """
    Validates Python object representation constraints.

    This validator is intentionally limited to REPRESENTATION concerns:
    - dataclass discipline
    - frozen discipline
    - slots discipline
    - __dict__ exposure
    - __weakref__ exposure

    It does NOT validate:
    - deep immutability
    - forbidden domain-level runtime types
    - business semantics
    """

    if inspect.isabstract(cls):
        return

    if require_dataclass and not is_dataclass(cls):
        raise StructuralContractViolation(f"{cls.__name__} must be a dataclass.")

    params = getattr(cls, "__dataclass_params__", None)

    if require_frozen:
        if not params or not getattr(params, "frozen", False):
            raise StructuralContractViolation(
                f"{cls.__name__} must be declared with frozen=True."
            )

    if require_slots and not hasattr(cls, "__slots__"):
        raise StructuralContractViolation(
            f"{cls.__name__} must declare a slots-based instance layout."
        )

    slots = _collect_all_slots(cls)

    if forbid_instance_dict and "__dict__" in slots:
        raise StructuralContractViolation(
            f"{cls.__name__} exposes __dict__ via __slots__, which is forbidden."
        )

    if forbid_weakref and "__weakref__" in slots:
        raise StructuralContractViolation(
            f"{cls.__name__} exposes __weakref__, which is forbidden."
        )

    _assert_instance_layout_is_dict_free(
        cls,
        forbid_instance_dict=forbid_instance_dict,
    )
