"""Typed YAML configuration loading for the Phase 1 foundation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from marketpilot.fx import FxSeed, build_fx_seed
from marketpilot.safety import validate_safety_config
from marketpilot.timeframes import StrategyMode, parse_strategy_mode


@dataclass(frozen=True)
class EnvironmentConfig:
    name: str
    paper_trading_only: bool
    fx_seed: FxSeed


@dataclass(frozen=True)
class StrategyConfig:
    mode: StrategyMode
    paper_trading_only: bool
    enabled_setups: tuple[str, ...]
    default_mode: StrategyMode = StrategyMode.DAILY_ONLY


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


def load_strategy_config(path: str | Path) -> StrategyConfig:
    """Load the central StrategyMode configuration and fail closed."""

    loaded = load_yaml_file(path)
    raw_strategy = loaded.get("strategy")
    if not isinstance(raw_strategy, dict):
        raise ValueError("strategy section is required.")

    validate_safety_config(raw_strategy)
    if raw_strategy.get("paper_trading_only") is not True:
        raise ValueError("strategy.paper_trading_only must be true.")

    raw_mode = raw_strategy.get("mode")
    mode = parse_strategy_mode(raw_mode)
    default_mode = parse_strategy_mode(raw_strategy.get("default_mode", StrategyMode.DAILY_ONLY.value))
    if default_mode is not StrategyMode.DAILY_ONLY:
        raise ValueError("strategy.default_mode must be daily_only.")

    environment_mode = raw_strategy.get("environment_mode")
    if environment_mode in {"backtest", "shadow", "paper"}:
        raise ValueError("strategy mode must be separate from environment mode.")

    enabled_setups = raw_strategy.get("enabled_setups", [])
    if not isinstance(enabled_setups, list) or any(not isinstance(item, str) for item in enabled_setups):
        raise ValueError("strategy.enabled_setups must be a list of setup names.")

    return StrategyConfig(
        mode=mode,
        paper_trading_only=True,
        enabled_setups=tuple(enabled_setups),
        default_mode=default_mode,
    )
