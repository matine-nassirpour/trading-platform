from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.architecture.role_rules import ROLE_RULES


def _enforce_dataclass_requirement(cls: type, role: DomainRole, rule) -> None:
    if rule.must_be_dataclass and not hasattr(cls, "__dataclass_fields__"):
        raise TypeError(f"{cls.__name__} ({role.value}) must be a dataclass")


def _enforce_state_rules(cls: type, role: DomainRole, rule) -> None:
    if not rule.allow_state and "__slots__" in cls.__dict__ and cls.__slots__:
        raise TypeError(f"{cls.__name__} ({role.value}) must not declare state")


def _enforce_method_rules(cls: type, role: DomainRole, rule) -> None:
    if rule.allow_public_domain_methods:
        return

    for name, member in cls.__dict__.items():
        if not callable(member):
            continue

        # Always allow:
        # - dunder methods
        # - private methods
        if name.startswith("__") or name.startswith("_"):
            continue

        # Public callable → forbidden
        raise TypeError(
            f"{cls.__name__} ({role.value}) must not define public domain methods "
            f"('{name}'). Only private or dunder methods are allowed."
        )


def _enforce_mutation_rules(cls: type, role: DomainRole, rule) -> None:
    if not rule.allow_mutation and "__setattr__" in cls.__dict__:
        raise TypeError(f"{cls.__name__} ({role.value}) must not override __setattr__")


def _enforce_slots(cls: type, role: DomainRole, rule) -> None:
    if rule.must_use_slots:
        if "__slots__" not in cls.__dict__:
            raise TypeError(f"{cls.__name__} ({role.value}) must declare __slots__")

        slots = cls.__dict__["__slots__"]

        if slots is None or slots == ():
            raise TypeError(
                f"{cls.__name__} ({role.value}) must not have empty __slots__"
            )


def _enforce_no_dict(cls: type, role: DomainRole, rule) -> None:
    if not rule.forbid_dict:
        return

    # Must define __slots__
    if "__slots__" not in cls.__dict__:
        raise TypeError(
            f"{cls.__name__} ({role.value}) must declare __slots__ to forbid __dict__"
        )

    slots = cls.__dict__["__slots__"]

    if isinstance(slots, str):
        slots = (slots,)

    if "__dict__" in slots:
        raise TypeError(
            f"{cls.__name__} ({role.value}) must not include '__dict__' in __slots__"
        )


def enforce_domain_role(cls: type) -> None:
    role = cls.role()
    rule = ROLE_RULES[role]

    _enforce_dataclass_requirement(cls, role, rule)
    _enforce_state_rules(cls, role, rule)
    _enforce_method_rules(cls, role, rule)
    _enforce_mutation_rules(cls, role, rule)
    _enforce_slots(cls, role, rule)
    _enforce_no_dict(cls, role, rule)
