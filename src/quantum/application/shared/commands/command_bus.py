import logging

from dataclasses import dataclass
from typing import Any, Generic, TypeVar, final

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.application.shared.errors.application_error import (
    ApplicationError,
    UseCaseError,
)

LOGGER = logging.getLogger(__name__)

C = TypeVar("C", bound=BaseCommand)
R = TypeVar("R")


# --- Command Handler Protocol -----------------------------------------------


class CommandHandler(Generic[C, R]):
    """
    Contract for all command handlers.

    Strict guarantees:

    - Deterministic execution
    - No side-effects outside transactional boundary
    - Application layer only
    """

    def handle(self, command: C) -> R:
        raise NotImplementedError


# --- Registration container --------------------------------------------------


@dataclass(frozen=True, slots=True)
class _HandlerBinding(Generic[C, R]):
    """
    Immutable handler binding.
    """

    command_type: type[C]
    handler: CommandHandler[C, R]


# --- Command Bus -------------------------------------------------------------


@final
class CommandBus:
    """
    Industry-grade synchronous Command Bus.

    Guarantees:
    - Deterministic dispatch
    - Single handler per command (strict CQRS)
    - Full type safety
    - Audit-ready execution tracing
    - Clean Architecture compliant

    Explicit non-goals:
    - No async
    - No retry logic
    - No infrastructure coupling

    These belong outside the Application layer.
    """

    __slots__ = ("_handlers",)

    def __init__(self) -> None:

        # strict one handler per command
        self._handlers: dict[type[BaseCommand], CommandHandler[Any, Any]] = {}

    # --- Registration -------------------------------------------------------

    def register(
        self,
        command_type: type[C],
        handler: CommandHandler[C, R],
    ) -> None:
        """
        Register handler.

        Must be called during bootstrap only.
        """

        if command_type in self._handlers:
            raise RuntimeError(
                f"Handler already registered for command '{command_type.__name__}'"
            )

        self._handlers[command_type] = handler

        LOGGER.debug(
            "CommandBus registered handler '%s' for command '%s'",
            handler.__class__.__name__,
            command_type.__name__,
        )

    # --- Dispatch -----------------------------------------------------------

    def dispatch(self, command: C) -> R:
        """
        Dispatch command synchronously.

        Fully deterministic.

        Raises:

        - UseCaseError if handler missing
        - ApplicationError propagated from handler
        """

        command_type = type(command)

        handler = self._handlers.get(command_type)

        if handler is None:

            LOGGER.error(
                "CommandBus: no handler registered for command '%s'",
                command_type.__name__,
            )

            raise UseCaseError(
                f"No handler registered for command '{command_type.__name__}'"
            )

        LOGGER.debug(
            "CommandBus dispatching command '%s' with handler '%s'",
            command_type.__name__,
            handler.__class__.__name__,
        )

        try:

            result = handler.handle(command)

            LOGGER.debug(
                "CommandBus successfully executed command '%s'",
                command_type.__name__,
            )

            return result

        except ApplicationError:

            # expected, propagate
            raise

        except Exception as exc:

            LOGGER.exception(
                "CommandBus fatal failure during command '%s'",
                command_type.__name__,
            )

            raise RuntimeError(
                f"Fatal error executing command '{command_type.__name__}'"
            ) from exc

    # --- Introspection ------------------------------------------------------

    def is_registered(self, command_type: type[BaseCommand]) -> bool:
        return command_type in self._handlers

    def registered_commands(self) -> list[type[BaseCommand]]:
        return list(self._handlers.keys())
