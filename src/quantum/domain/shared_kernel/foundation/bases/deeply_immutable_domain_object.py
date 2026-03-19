from abc import abstractmethod
from typing import ClassVar

from quantum.domain.shared_kernel.foundation.bases.validated_domain_object import (
    ValidatedDomainObject,
)
from quantum.domain.shared_kernel.foundation.contracts.policies import StructuralPolicy
from quantum.domain.shared_kernel.foundation.contracts.structural_policy import (
    CompositeStructuralPolicy,
    DeepImmutabilityPolicy,
    PythonDataclassRepresentationPolicy,
)


class DeeplyImmutableDomainObject(ValidatedDomainObject):
    """
    Structural base for domain objects whose full field graph must satisfy
    the deep-immutability policy.

    Typical examples:
    - Value Objects
    - AggregateState
    - Domain Events
    - snapshots
    - cursors
    """

    __slots__ = ()

    __structural_policy__: ClassVar[StructuralPolicy] = CompositeStructuralPolicy(
        policies=(
            PythonDataclassRepresentationPolicy(),
            DeepImmutabilityPolicy(),
        )
    )

    @abstractmethod
    def _validate_semantics(self) -> None:
        raise NotImplementedError
