from abc import ABC

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.architecture.domain_object import DomainObject


class ReadModel(DomainObject, ABC):
    """
    Base class for all CQRS read-side models.

    A ReadModel:
    - Is NOT a domain concept
    - Has NO business invariants
    - Is fully derived from events
    - Exists only for querying / reporting
    - Is never referenced by Aggregates or Policies
    """

    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.READ_MODEL
