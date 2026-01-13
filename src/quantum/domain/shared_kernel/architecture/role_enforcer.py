from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.architecture.role_rules import ROLE_RULES


def _enforce_dataclass_requirement(cls: type, role: DomainRole, rule) -> None:
    if rule.must_be_dataclass and not hasattr(cls, "__dataclass_fields__"):
        raise TypeError(f"{cls.__name__} ({role.value}) must be a dataclass")


def _enforce_state_rules(cls: type, role: DomainRole, rule) -> None:
    if not rule.allow_state and "__slots__" in cls.__dict__ and cls.__slots__:
        raise TypeError(f"{cls.__name__} ({role.value}) must not declare state")


def _enforce_method_rules(cls: type, role: DomainRole, rule) -> None:
    if not rule.allow_methods:
        for name, member in cls.__dict__.items():
            if callable(member) and not name.startswith("_"):
                raise TypeError(
                    f"{cls.__name__} ({role.value}) must not define methods ({name})"
                )


def _enforce_mutation_rules(cls: type, role: DomainRole, rule) -> None:
    if not rule.allow_mutation and "__setattr__" in cls.__dict__:
        raise TypeError(f"{cls.__name__} ({role.value}) must not override __setattr__")


def enforce_domain_role(cls: type) -> None:
    role = cls.role()
    rule = ROLE_RULES[role]

    _enforce_dataclass_requirement(cls, role, rule)
    _enforce_state_rules(cls, role, rule)
    _enforce_method_rules(cls, role, rule)
    _enforce_mutation_rules(cls, role, rule)
