"""Setup contracts for deterministic, paper-only strategy research."""

from marketpilot.setups.base import (
    NumericEvidence,
    SetupRejectionReason,
    SetupResult,
    SetupStatus,
    SetupTiming,
)
from marketpilot.setups.relative_strength import (
    RelativeStrengthInput,
    evaluate_relative_strength_leader,
)

__all__ = [
    "NumericEvidence",
    "SetupRejectionReason",
    "SetupResult",
    "SetupStatus",
    "SetupTiming",
    "RelativeStrengthInput",
    "evaluate_relative_strength_leader",
]
