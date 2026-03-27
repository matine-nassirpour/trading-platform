from abc import ABC

from quantum.domain.shared_kernel.foundation.bases.canonical_domain_state_object import (
    CanonicalDomainStateObject,
)


class ValueObject(CanonicalDomainStateObject, ABC):
    """
    Canonical base class for all Value Objects.
    """

    __slots__ = ()
