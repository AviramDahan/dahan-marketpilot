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
from marketpilot.setups.trend_pullback import (
    TrendPullbackInput,
    evaluate_trend_pullback,
)
from marketpilot.setups.volume_breakout import (
    VolumeBreakoutInput,
    evaluate_volume_breakout,
)

__all__ = [
    "NumericEvidence",
    "SetupRejectionReason",
    "SetupResult",
    "SetupStatus",
    "SetupTiming",
    "TrendPullbackInput",
    "evaluate_trend_pullback",
    "VolumeBreakoutInput",
    "evaluate_volume_breakout",
    "RelativeStrengthInput",
    "evaluate_relative_strength_leader",
]
