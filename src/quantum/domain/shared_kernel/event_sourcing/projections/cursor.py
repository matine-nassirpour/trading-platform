from abc import ABC
from dataclasses import dataclass

from quantum.domain.shared_kernel.foundation.bases.deeply_immutable_domain_object import (
    DeeplyImmutableDomainObject,
)


@dataclass(frozen=True, slots=True)
class Cursor(DeeplyImmutableDomainObject, ABC):
    """
    Monotonic, audit-grade cursor.

    A Cursor represents a strictly ordered position in a domain stream
    (e.g. event sequence, market feed, projection replay, etc).
    """
