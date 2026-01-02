from dataclasses import dataclass, replace

from quantum.domain.shared.errors.invariants import InvariantViolation
from quantum.domain.shared.temporal.temporal_validity import TemporalValidity
from quantum.domain.shared.value_objects.epoch_ms import EpochMs


@dataclass(frozen=True)
class TemporalEntity:
    """
    Mixin for entities / aggregates with explicit temporal validity.
    """

    validity: TemporalValidity

    def _validate_temporal(self) -> None:
        if not isinstance(self.validity, TemporalValidity):
            raise InvariantViolation("TemporalEntity requires TemporalValidity")

    def close_validity(self, *, at: EpochMs):
        """
        Returns a new instance with closed temporal validity.
        """
        return replace(
            self,
            validity=self.validity.close(at=at),
        )
