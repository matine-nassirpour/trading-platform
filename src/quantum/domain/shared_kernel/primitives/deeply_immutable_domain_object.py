from abc import abstractmethod

from quantum.domain.shared_kernel.primitives.structural_contract import (
    _assert_deep_immutability_of_instance_fields,
)
from quantum.domain.shared_kernel.primitives.validated_domain_object import (
    ValidatedDomainObject,
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

    def _before_validate(self) -> None:
        super()._before_validate()
        _assert_deep_immutability_of_instance_fields(self)

    @abstractmethod
    def _validate(self) -> None:
        """
        Must be implemented by concrete subclasses.
        """
        raise NotImplementedError
