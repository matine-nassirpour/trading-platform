from __future__ import annotations

from quantum.domain.risk.events.v1.killswitch_trigger_event import (
    KillSwitchTriggerEvent,
)
from quantum.domain.risk.value_objects.kill_switch_reason import KillSwitchReason
from quantum.domain.risk.value_objects.kill_switch_status import KillSwitchStatus
from quantum.domain.shared_kernel.errors.invariants import (
    InvalidStateTransition,
    InvariantViolation,
)
from quantum.domain.shared_kernel.primitives.event_sourced_aggregate_root import (
    EventSourcedAggregateRoot,
)
from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs


class KillSwitchState(EventSourcedAggregateRoot):
    """
    Aggregate Root representing a global trading kill switch.

    Properties:
    - Latched once triggered
    - Explicit trigger cause
    - Deterministic reset rules
    """

    # --- Factory --------------------------------------------------------------

    @staticmethod
    def armed() -> KillSwitchState:
        ks = KillSwitchState.__new__(KillSwitchState)
        EventSourcedAggregateRoot.__init__(ks)

        ks.status = KillSwitchStatus.armed()
        ks.triggered_at = None
        ks.reason = None

        ks._validate_state()
        return ks

    # --- Commands -------------------------------------------------------------

    def trigger(
        self,
        *,
        at: EpochMs,
        reason: KillSwitchReason,
        detail: str | None = None,
    ) -> None:
        if self.status == KillSwitchStatus.triggered():
            raise InvalidStateTransition("KillSwitch already triggered")

        self._raise(
            KillSwitchTriggerEvent(
                occurred_at=at,
                reason=reason,
                detail=detail,
            )
        )

    # --- Event application ----------------------------------------------------

    def _apply_killswitchtriggerevent(self, event: KillSwitchTriggerEvent) -> None:
        self.status = KillSwitchStatus.triggered()
        self.triggered_at = event.occurred_at
        self.reason = event.reason

    # --- Invariants ----------------------------------------------------------

    def _validate_state(self) -> None:
        if not isinstance(self.status, KillSwitchStatus):
            raise InvariantViolation("KillSwitchState must have a valid status")

        if self.status == KillSwitchStatus.triggered():
            if self.triggered_at is None or self.reason is None:
                raise InvariantViolation(
                    "Triggered KillSwitch must have timestamp and reason"
                )

        if self.status == KillSwitchStatus.armed():
            if self.triggered_at is not None or self.reason is not None:
                raise InvariantViolation(
                    "Armed KillSwitch must not carry trigger metadata"
                )
