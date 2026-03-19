from abc import abstractmethod

from quantum.domain.shared_kernel.foundation.bases.validated_domain_object import (
    ValidatedDomainObject,
)
from quantum.domain.shared_kernel.foundation.contracts.structural_contract import (
    _assert_deep_immutability_of_instance_fields,
)


class DeeplyImmutableDomainObject(ValidatedDomainObject):
    """
    Structural base for domain objects whose full field graph must satisfy
    the deep-immutability contract.

    Typical examples:
    - Value Objects
    - AggregateState
    - Domain Events
    - Cursors
    """

    __slots__ = ()

    def _validate_structure(self) -> None:
        super()._validate_structure()
        _assert_deep_immutability_of_instance_fields(self)

    @abstractmethod
    def _validate(self) -> None:
        """
        Must be implemented by concrete subclasses.
        """
        raise NotImplementedError
