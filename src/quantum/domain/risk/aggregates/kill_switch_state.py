from __future__ import annotations

from quantum.domain.risk.events.v1.killswitch_armed_event import KillSwitchArmedEvent
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
    Fully event-sourced Kill Switch.

    All state MUST come from events.
    """

    status: KillSwitchStatus
    triggered_at: EpochMs | None
    reason: KillSwitchReason | None

    # --- Factory --------------------------------------------------------------

    @staticmethod
    def arm(*, at: EpochMs) -> KillSwitchState:
        ks = KillSwitchState.__new__(KillSwitchState)
        EventSourcedAggregateRoot.__init__(ks)

        ks._raise(KillSwitchArmedEvent(occurred_at=at))
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

    def _apply_killswitcharmedevent(self, event: KillSwitchArmedEvent) -> None:
        self.status = KillSwitchStatus.armed()
        self.triggered_at = None
        self.reason = None

    def _apply_killswitchtriggerevent(self, event: KillSwitchTriggerEvent) -> None:
        self.status = KillSwitchStatus.triggered()
        self.triggered_at = event.occurred_at
        self.reason = event.reason

    # --- Invariants ----------------------------------------------------------

    def _validate_state(self) -> None:
        if not isinstance(self.status, KillSwitchStatus):
            raise InvariantViolation("KillSwitchState must have a valid status")

        if self.status == KillSwitchStatus.armed():
            if self.triggered_at is not None or self.reason is not None:
                raise InvariantViolation(
                    "Armed KillSwitch must not have trigger metadata"
                )

        if self.status == KillSwitchStatus.triggered():
            if self.triggered_at is None or self.reason is None:
                raise InvariantViolation(
                    "Triggered KillSwitch must have timestamp and reason"
                )
