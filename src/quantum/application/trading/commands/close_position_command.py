from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.market.instrument.instrument_spec import InstrumentSpec
from quantum.domain.shared_kernel.modeling.monetary.price import Price
from quantum.domain.trading.position.aggregate import PositionId


@dataclass(frozen=True, slots=True)
class ClosePositionCommand(BaseCommand):
    """
    Command: close an opened Position aggregate and compute realized PnL.
    """

    position_id: PositionId
    exit_price: Price
    instrument: InstrumentSpec
