from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EvaluateRiskCommand:
    """
    Intent to evaluate current risk state.
    """
