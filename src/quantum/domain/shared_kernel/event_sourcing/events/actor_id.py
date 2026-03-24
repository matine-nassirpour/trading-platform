from __future__ import annotations

import re

from dataclasses import dataclass

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject

_ACTOR_ID_RE = re.compile(
    r"^(?P<namespace>[a-z][a-z0-9_-]{0,31}):"
    r"(?P<identifier>[a-z0-9]+(?:[._-][a-z0-9]+)*)$"
)


@dataclass(frozen=True, slots=True)
class ActorId(ValueObject):
    """
    Canonical audit-grade actor identifier.

    Format:
        <namespace>:<identifier>

    Examples:
        - strategy:mean_reversion_v3
        - system:risk_engine
        - user:trader_42
        - scheduler:daily-close
        - service:execution.router

    HARD GUARANTEES:
    - string only
    - no surrounding whitespace
    - no internal whitespace
    - exactly one colon
    - non-empty namespace
    - non-empty identifier
    - canonical lowercase representation
    - deterministic parsing
    """

    value: str

    def _validate_semantics(self) -> None:
        if not isinstance(self.value, str):
            raise InvariantViolation("ActorId must be a string")

        canonical = self.value.strip().lower()

        if not canonical:
            raise InvariantViolation("ActorId must not be empty")

        if any(ch.isspace() for ch in canonical):
            raise InvariantViolation("ActorId must not contain whitespace")

        match = _ACTOR_ID_RE.fullmatch(canonical)
        if match is None:
            raise InvariantViolation(
                "ActorId must match canonical format '<namespace>:<identifier>' "
                "with exactly one colon, lowercase canonical form, and no empty segments"
            )

        object.__setattr__(self, "value", canonical)

    def namespace(self) -> str:
        return self.value.split(":", 1)[0]

    def identifier(self) -> str:
        return self.value.split(":", 1)[1]

    def __str__(self) -> str:
        return self.value

    @staticmethod
    def strategy(strategy_name: str) -> ActorId:
        return ActorId(f"strategy:{strategy_name}")

    @staticmethod
    def system(component_name: str) -> ActorId:
        return ActorId(f"system:{component_name}")

    @staticmethod
    def user(user_name: str) -> ActorId:
        return ActorId(f"user:{user_name}")

    @staticmethod
    def scheduler(job_name: str) -> ActorId:
        return ActorId(f"scheduler:{job_name}")

    @staticmethod
    def service(service_name: str) -> ActorId:
        return ActorId(f"service:{service_name}")
