"""Typed YAML configuration loading for the Phase 1 foundation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from marketpilot.fx import FxSeed, build_fx_seed
from marketpilot.safety import validate_safety_config


@dataclass(frozen=True)
class EnvironmentConfig:
    name: str
    paper_trading_only: bool
    fx_seed: FxSeed


def load_yaml_file(path: str | Path) -> dict[str, Any]:
    """Load YAML safely and return an empty mapping for blank files."""

    with Path(path).open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise ValueError("Configuration root must be a mapping.")
    validate_safety_config(loaded)
    return loaded


def load_environment_config(path: str | Path) -> EnvironmentConfig:
    """Load and validate one environment YAML file."""

    loaded = load_yaml_file(path)
    raw_environment = loaded.get("environment")
    if not isinstance(raw_environment, dict):
        raise ValueError("environment section is required.")

    validate_safety_config(raw_environment)
    fx_seed = build_fx_seed(raw_environment)
    name = str(raw_environment.get("name", "")).strip()
    if name not in {"backtest", "shadow", "paper"}:
        raise ValueError("environment.name must be one of backtest, shadow, or paper.")

    return EnvironmentConfig(
        name=name,
        paper_trading_only=raw_environment.get("paper_trading_only") is True,
        fx_seed=fx_seed,
    )
