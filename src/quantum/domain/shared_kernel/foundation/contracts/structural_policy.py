from dataclasses import dataclass
from functools import cache

from quantum.domain.shared_kernel.foundation.contracts.deep_immutability import (
    validate_deep_immutability_of_dataclass_instance,
)
from quantum.domain.shared_kernel.foundation.contracts.policies import StructuralPolicy
from quantum.domain.shared_kernel.foundation.contracts.representation import (
    validate_python_dataclass_representation,
)


@cache
def _validate_composite_policy_class(
    policies: tuple[StructuralPolicy, ...],
    cls: type,
) -> None:
    """
    Cached class-level validation for a composite structural policy.

    IMPORTANT:
    The cache is intentionally module-level, not method-level, to avoid
    retaining `self` references and triggering B019-like memory retention
    patterns on bound methods.

    Cache key:
    - the immutable tuple of structural policies
    - the target class

    This function must remain pure and side-effect free.
    """
    for policy in policies:
        policy.validate_class(cls)


@dataclass(frozen=True, slots=True)
class PythonDataclassRepresentationPolicy(StructuralPolicy):
    """
    Structural policy dedicated strictly to Python representation discipline.
    """

    require_dataclass: bool = True
    require_frozen: bool = True
    require_slots: bool = True
    forbid_instance_dict: bool = True
    forbid_weakref: bool = True

    def validate_class(self, cls: type) -> None:
        validate_python_dataclass_representation(
            cls,
            require_dataclass=self.require_dataclass,
            require_frozen=self.require_frozen,
            require_slots=self.require_slots,
            forbid_instance_dict=self.forbid_instance_dict,
            forbid_weakref=self.forbid_weakref,
        )

    def validate_instance(self, instance: object) -> None:
        return None


@dataclass(frozen=True, slots=True)
class DeepImmutabilityPolicy(StructuralPolicy):
    """
    Structural policy dedicated strictly to deep immutability of instance state.
    """

    def validate_class(self, cls: type) -> None:
        return None

    def validate_instance(self, instance: object) -> None:
        validate_deep_immutability_of_dataclass_instance(instance)


@dataclass(frozen=True, slots=True)
class CompositeStructuralPolicy(StructuralPolicy):
    """
    Composes multiple orthogonal structural policies.

    Order matters:
    - representation policies should typically run before instance graph policies
    - class-level validation is cached by target class and policy tuple
    """

    policies: tuple[StructuralPolicy, ...]

    def validate_class(self, cls: type) -> None:
        _validate_composite_policy_class(self.policies, cls)

    def validate_instance(self, instance: object) -> None:
        _validate_composite_policy_class(self.policies, type(instance))

        for policy in self.policies:
            policy.validate_instance(instance)
