from abc import ABC

from quantum.domain.shared_kernel.foundation.bases.deeply_immutable_domain_object import (
    DeeplyImmutableDomainObject,
)


class ValueObject(DeeplyImmutableDomainObject, ABC):
    """
    Canonical base class for all Value Objects.
    """

    __slots__ = ()
