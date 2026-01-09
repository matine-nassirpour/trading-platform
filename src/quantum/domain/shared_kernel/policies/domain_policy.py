from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.architecture.domain_object import DomainObject


class DomainPolicy(DomainObject):
    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.POLICY
