from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from quantum.application.commands.command_result import CommandResult

C = TypeVar("C")
R = TypeVar("R")


class CommandHandler(ABC, Generic[C, R]):
    """
    Canonical command handler interface.
    """

    @abstractmethod
    def handle(self, command: C) -> CommandResult[R]:
        raise NotImplementedError
