from quantum.application.commands.command_result import CommandResult
from quantum.application.commands.decision.register_no_trade_command import (
    RegisterNoTradeCommand,
)
from quantum.application.errors.application_error import DomainExecutionError
from quantum.application.handlers.base_handler import CommandHandler
from quantum.application.ports.outbound.event_store import EventStore
from quantum.domain.decision.events.v1.no_trade_decision_event import (
    NoTradeDecisionEvent,
)


class RegisterNoTradeHandler(CommandHandler[RegisterNoTradeCommand, None]):

    def __init__(self, event_store: EventStore, envelope_factory) -> None:
        self._event_store = event_store
        self._envelope_factory = envelope_factory

    def handle(self, command: RegisterNoTradeCommand) -> CommandResult[None]:

        try:
            event = NoTradeDecisionEvent(
                symbol=command.symbol,
                decision_identity=command.decision_identity,
                no_trade_decision=command.outcome,
            )

            envelope = self._envelope_factory.wrap(event)

            self._event_store.append([envelope])

            return CommandResult()

        except Exception as exc:
            raise DomainExecutionError(exc) from None
