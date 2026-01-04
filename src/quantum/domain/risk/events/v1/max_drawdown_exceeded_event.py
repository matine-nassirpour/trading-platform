from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.risk.value_objects.drawdown import Drawdown
from quantum.domain.shared_kernel.events.base_event import BaseEvent
from quantum.domain.shared_kernel.primitives.monetary_amount import MonetaryAmount


@dataclass(frozen=True)
class MaxDrawdownExceededEvent(BaseEvent):
    """
    Emitted when the drawdown exceeds or equals the configured maximum.

    Convention:
    - drawdown is ALWAYS positive (peak - equity)
    """

    event_name: ClassVar[str] = "risk.max_drawdown_exceeded"
    event_version: ClassVar[int] = 1

    current_drawdown: Drawdown
    limit: MonetaryAmount
