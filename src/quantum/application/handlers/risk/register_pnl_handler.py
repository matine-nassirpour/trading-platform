from quantum.application.commands.command_result import CommandResult
from quantum.application.commands.risk.register_pnl_command import RegisterPnLCommand
from quantum.application.errors.application_error import DomainExecutionError
from quantum.application.handlers.base_handler import CommandHandler
from quantum.application.ports.outbound.event_store import EventStore
from quantum.application.ports.outbound.unit_of_work import UnitOfWork
from quantum.domain.risk.governance.aggregates.risk_state import RiskState


class RegisterPnLHandler(CommandHandler[RegisterPnLCommand, None]):

    def __init__(
        self,
        event_store: EventStore,
        unit_of_work: UnitOfWork,
        risk_repository,
        envelope_factory,
    ) -> None:

        self._event_store = event_store
        self._unit_of_work = unit_of_work
        self._risk_repository = risk_repository
        self._envelope_factory = envelope_factory

    def handle(self, command: RegisterPnLCommand) -> CommandResult[None]:

        try:
            aggregate: RiskState = self._risk_repository.load()

            events = aggregate.register_pnl(
                pnl=command.pnl,
                drawdown=command.drawdown,
                daily_loss=command.daily_loss,
                exposure=command.exposure,
                notional=command.notional,
            )

            envelopes = [self._envelope_factory.wrap(e) for e in events]

            self._event_store.append(envelopes)

            self._unit_of_work.commit()

            return CommandResult()

        except Exception as exc:
            self._unit_of_work.rollback()
            raise DomainExecutionError(exc) from None
