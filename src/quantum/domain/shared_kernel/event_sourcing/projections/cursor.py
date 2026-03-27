from abc import ABC
from dataclasses import dataclass

from quantum.domain.shared_kernel.foundation.bases.canonical_domain_state_object import (
    CanonicalDomainStateObject,
)


@dataclass(frozen=True, slots=True)
class Cursor(CanonicalDomainStateObject, ABC):
    """
    Monotonic, audit-grade cursor.

    A Cursor represents a strictly ordered position in a domain stream
    (e.g. event sequence, market feed, projection replay, etc).
    """
