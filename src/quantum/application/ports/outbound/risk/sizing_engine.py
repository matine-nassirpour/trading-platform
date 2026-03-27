from abc import abstractmethod
from typing import Protocol, runtime_checkable

from quantum.domain.decision.qualification.decision_qualification import (
    DecisionQualification,
)
from quantum.domain.market.instrument.identity.symbol import Symbol
from quantum.domain.trading.value_objects.volume import PositiveVolume


@runtime_checkable
class SizingEngine(Protocol):
    """
    Application engine responsible for sizing calculation.
    """

    @abstractmethod
    def compute_volume(
        self,
        symbol: Symbol,
        decision_identity: DecisionQualification,
    ) -> PositiveVolume:
        raise NotImplementedError
