from __future__ import annotations

import re

from dataclasses import dataclass

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject

_ACTOR_ID_RE = re.compile(
    r"^(?P<namespace>[a-z][a-z0-9_-]{0,31}):"
    r"(?P<identifier>[a-z0-9]+(?:[._-][a-z0-9]+)*)$"
)


def _canonicalize(value: str) -> str:
    return value.strip().lower()


def _is_canonical(value: str) -> bool:
    return value == _canonicalize(value)


@dataclass(frozen=True, slots=True)
class ActorId(ValueObject):
    """
    Canonical audit-grade actor identifier.

    Format:
        <namespace>:<identifier>

    IMPORTANT:
    This object does NOT normalize input.

    Accepted:
    - ActorId("strategy:mean_reversion_v3")
    - ActorId("system:risk_engine")
    - ActorId("service:execution.router")

    Rejected:
    - ActorId(" Strategy:Mean_Reversion ")
    - ActorId("strategy:Mean_Reversion")
    - ActorId(" system:risk_engine ")
    """

    value: str

    def _validate_semantics(self) -> None:
        if not isinstance(self.value, str):
            raise InvariantViolation("ActorId must be a string.")

        if not self.value:
            raise InvariantViolation("ActorId must not be empty.")

        if not _is_canonical(self.value):
            raise InvariantViolation(
                f"ActorId must already be canonical. "
                f"Got {self.value!r}, expected {_canonicalize(self.value)!r}. "
                "Normalization must happen outside the domain."
            )

        if any(ch.isspace() for ch in self.value):
            raise InvariantViolation("ActorId must not contain whitespace.")

        if _ACTOR_ID_RE.fullmatch(self.value) is None:
            raise InvariantViolation(
                "ActorId must match canonical format '<namespace>:<identifier>' "
                "with exactly one colon, lowercase canonical form, and no empty segments."
            )

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
