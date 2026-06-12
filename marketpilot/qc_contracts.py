"""Documented QuantConnect API contract names for Phase 2 local tests."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QuantConnectContract:
    allowed_names: tuple[str, ...]
    forbidden_names: tuple[str, ...]
    notes: tuple[str, ...]


PHASE2_QC_CONTRACT = QuantConnectContract(
    allowed_names=(
        "add_universe",
        "Fundamental",
        "add_equity",
        "history",
        "indicator readiness",
        "manual indicator cleanup",
        "consolidator cleanup",
    ),
    forbidden_names=(
        "AddUniverse legacy coarse/fine assumption",
        "cloud backtest execution",
        "Paper deployment",
        "live deployment",
        "brokerage settings",
        "repository credentials",
    ),
    notes=(
        "Local Phase 2 tests do not import QuantConnect runtime modules.",
        "Current fundamental universe docs use add_universe with Fundamental records.",
        "Dynamic universes require manual indicator/consolidator cleanup.",
    ),
)

