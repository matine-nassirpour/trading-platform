from typing import Protocol, runtime_checkable

from quantum.application.shared.commands.command_id import CommandId


@runtime_checkable
class CommandDeduplicationRepository(Protocol):
    """
    Transaction-bound command deduplication repository.

    Responsibility:
    - Ensure a mutating command is processed at most once.
    - Must be used inside the same UnitOfWork as aggregate mutation.
    - Must enforce uniqueness at storage level.

    Critical invariant:
    - reserve(command_id) must be atomic.
    - If command_id already exists, it must return False.
    - If command_id is new, it must reserve it and return True.
    """

    async def reserve(self, command_id: CommandId) -> bool: ...
