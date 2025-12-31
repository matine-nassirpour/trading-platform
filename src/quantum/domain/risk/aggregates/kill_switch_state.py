from __future__ import annotations

from dataclasses import dataclass, replace

from quantum.domain.risk.events.v1.killswitch_trigger_event import (
    KillSwitchTriggerEvent,
)
from quantum.domain.risk.types.kill_switch_status import KillSwitchStatus
from quantum.domain.shared.errors.invariants import (
    InvalidStateTransition,
    InvariantViolation,
)
from quantum.domain.shared.primitives.aggregate_root import AggregateRoot
from quantum.domain.shared.value_objects.epoch_ms import EpochMs
from quantum.domain.types.enums import KillSwitchReason


@dataclass(frozen=True)
class KillSwitchState(AggregateRoot):
    """
    Aggregate Root representing a global trading kill switch.

    Properties:
    - Latched once triggered
    - Explicit trigger cause
    - Deterministic reset rules
    """

    status: KillSwitchStatus
    triggered_at: EpochMs | None = None
    reason: KillSwitchReason | None = None

    # --- Invariants -----------------------------------------------------------

    def _validate(self) -> None:
        if self.status == KillSwitchStatus.TRIGGERED:
            if self.triggered_at is None or self.reason is None:
                raise InvariantViolation(
                    "Triggered KillSwitch must have timestamp and reason"
                )

        if self.status == KillSwitchStatus.ARMED:
            if self.triggered_at is not None or self.reason is not None:
                raise InvariantViolation(
                    "Armed KillSwitch must not carry trigger metadata"
                )

    # --- Factories ------------------------------------------------------------

    @staticmethod
    def armed() -> KillSwitchState:
        """
        Canonical initial state.
        """
        return KillSwitchState(status=KillSwitchStatus.ARMED)

    # --- Commands -------------------------------------------------------------

    def trigger(
        self,
        *,
        at: EpochMs,
        reason: KillSwitchReason,
        detail: str | None = None,
    ) -> KillSwitchState:
        if self.status == KillSwitchStatus.TRIGGERED:
            raise InvalidStateTransition("KillSwitch already triggered")

        event = KillSwitchTriggerEvent(
            occurred_at=at.to_datetime(),
            trigger_epoch_ms=at,
            reason=reason,
            detail=detail,
        )

        return replace(
            self,
            status=KillSwitchStatus.TRIGGERED,
            triggered_at=at,
            reason=reason,
        )._raise(event)
