from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.risk.capital.capital_allocation_intent import (
    CapitalAllocationIntent,
)
from quantum.domain.shared_kernel.identifiers.intent_id import IntentId


@dataclass(frozen=True, slots=True)
class AllocateCapitalCommand(BaseCommand):
    intent_id: IntentId
    allocation: CapitalAllocationIntent
