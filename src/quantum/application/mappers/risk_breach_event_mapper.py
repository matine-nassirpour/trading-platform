from quantum.domain.risk.events.v1.risk_breach_event import RiskBreachEvent
from quantum.domain.risk.value_objects.risk_breach import RiskBreach
from quantum.domain.shared.value_objects.epoch_ms import EpochMs


class RiskBreachEventMapper:
    """
    Application-layer mapper converting RiskBreach value objects
    into publishable domain events.

    Responsibilities:
    - Preserve domain purity (no event creation in policies)
    - Centralize VO → Event translation
    - Ensure audit-safe and deterministic event emission
    """

    @staticmethod
    def to_event(
        *,
        breach: RiskBreach,
        at: EpochMs,
    ) -> RiskBreachEvent:
        return RiskBreachEvent(
            occurred_at=at.to_datetime(),
            breach=breach,
            trigger_epoch_ms=at,
        )
