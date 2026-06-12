"""Static dashboard state for the Phase 1 read-only shell."""

from __future__ import annotations

from dataclasses import dataclass

from marketpilot.constants import DISCLAIMER


@dataclass(frozen=True)
class DashboardSafetyState:
    title: str = "Dahan MarketPilot"
    disclaimer: str = DISCLAIMER
    paper_only_status: str = "Paper-only safety mode"
    read_only_status: str = "Read-only dashboard shell"
    data_status: str = "No live data connected"
    scope_note: str = "Phase 1 displays safety state only."


def default_safety_state() -> DashboardSafetyState:
    return DashboardSafetyState()
