from abc import abstractmethod
from typing import ClassVar

from quantum.domain.shared_kernel.foundation.bases.validated_domain_object import (
    ValidatedDomainObject,
)
from quantum.domain.shared_kernel.foundation.contracts.policies import StructuralPolicy
from quantum.domain.shared_kernel.foundation.contracts.structural_policy import (
    CanonicalDomainStatePolicy,
    CompositeStructuralPolicy,
    PythonDataclassRepresentationPolicy,
)


class CanonicalDomainStateObject(ValidatedDomainObject):
    """
    Structural base for canonical replay-safe domain state objects.

    This base enforces the canonical structural doctrine required for domain
    objects whose full field graph must remain:

    - representation-disciplined
    - deeply immutable
    - replay-safe
    - explicit in domain modeling

    GUARANTEES:
    - Python dataclass representation discipline
    - frozen instance semantics
    - slots-only instance layout
    - no instance __dict__
    - canonical domain-state validation over the full field graph
    """

    __slots__ = ()

    _STRUCTURAL_POLICY: ClassVar[StructuralPolicy] = CompositeStructuralPolicy(
        policies=(
            PythonDataclassRepresentationPolicy(),
            CanonicalDomainStatePolicy(),
        )
    )

    @abstractmethod
    def _validate_semantics(self) -> None:
        raise NotImplementedError
