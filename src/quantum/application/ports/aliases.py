from quantum.application.ports.outbound.event_publisher import DomainEventPublisher
from quantum.application.ports.outbound.kill_switch_repository import (
    KillSwitchRepository,
)
from quantum.application.ports.outbound.position_repository import PositionRepository
from quantum.application.ports.outbound.risk_state_repository import RiskStateRepository
from quantum.application.ports.outbound.trading_intent_repository import (
    TradingIntentRepository,
)
from quantum.application.ports.outbound.unit_of_work import UnitOfWork

__all__ = [
    "TradingIntentRepo",
    "OrderRepo",
    "PositionRepo",
    "RiskStateRepo",
    "KillSwitchRepo",
    "EventPublisher",
    "UoW",
]


TradingIntentRepo = TradingIntentRepository
OrderRepo = TradingIntentRepository  # if orders are stored separately, adjust later
PositionRepo = PositionRepository
RiskStateRepo = RiskStateRepository
KillSwitchRepo = KillSwitchRepository
EventPublisher = DomainEventPublisher
UoW = UnitOfWork
