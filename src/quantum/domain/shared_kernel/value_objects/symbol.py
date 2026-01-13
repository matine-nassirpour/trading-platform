import re

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.architecture.immutable_dataclass import (
    immutable_dataclass,
)
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.mutation_key import MutationKey
from quantum.domain.shared_kernel.primitives.value_object import ValueObject

_SYMBOL_RE = re.compile(r"^[A-Z0-9._\-]{3,20}$")


@immutable_dataclass
class Symbol(ValueObject):
    value: str

    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.VALUE_OBJECT

    def _validate_semantics(self, key: MutationKey) -> None:
        v = self.value.strip().upper()
        if not _SYMBOL_RE.match(v):
            raise InvariantViolation(f"Invalid symbol: {self.value}")
        object.__setattr__(self, "value", v)
