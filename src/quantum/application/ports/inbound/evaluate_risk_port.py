from typing import Protocol

from quantum.application.commands.evaluate_risk import EvaluateRiskCommand


class EvaluateRiskPort(Protocol):
    """
    Evaluates desk-level risk against configured limits.

    Responsibilities:
    - Load RiskState aggregate
    - Apply risk policies
    - Emit risk-related events if thresholds are breached
    """

    def execute(self, command: EvaluateRiskCommand) -> None: ...
