"""Volume Breakout setup contract with no trading side effects."""

from __future__ import annotations

from pathlib import Path

import yaml


SETUP_NAME = "volume_breakout"
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "volume_breakout.yaml"


def load_volume_breakout_config(path: str | Path = DEFAULT_CONFIG_PATH) -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    config = loaded.get("volume_breakout", loaded)
    if not isinstance(config, dict):
        raise ValueError("volume_breakout config must be a mapping.")
    if config.get("paper_trading_only") is not True:
        raise ValueError("volume_breakout config requires paper_trading_only: true.")
    if config.get("timing_mode") != "completed_daily_bar":
        raise ValueError("Volume Breakout must use completed_daily_bar timing.")
    disabled = config.get("disabled_behaviors", {})
    if disabled.get("intrabar_validity") is not False:
        raise ValueError("Volume Breakout must use completed daily bars only.")
    return config
