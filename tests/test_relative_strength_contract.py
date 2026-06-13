from datetime import datetime, timezone
from pathlib import Path

import pytest

from marketpilot.setups.base import SetupRejectionReason, SetupResult, SetupStatus
from marketpilot.setups.relative_strength import contract_result, load_relative_strength_config


def test_relative_strength_config_contains_safety_bounded_defaults():
    config = load_relative_strength_config()

    assert config["paper_trading_only"] is True
    assert config["timing_mode"] == "completed_daily_bar"
    assert config["benchmark"]["hard_gate"] == "SPY"
    assert config["benchmark"]["evidence_only"] == "QQQ"
    assert config["benchmark"]["required_windows"] == [20, 60]
    assert config["risk"]["max_52_week_high_distance_pct"] == 15.0
    assert config["disabled_behaviors"]["intrabar_validity"] is False
    assert config["disabled_behaviors"]["create_orders"] is False
    assert config["disabled_behaviors"]["portfolio_sizing"] is False
    assert config["disabled_behaviors"]["buy_watch_avoid_classifications"] is False
    assert config["disabled_behaviors"]["backtest_result_creation"] is False
    assert config["disabled_behaviors"]["telegram_delivery"] is False
    assert config["disabled_behaviors"]["paper_deployment"] is False
    assert config["disabled_behaviors"]["live_deployment"] is False


def test_relative_strength_config_fails_closed_for_unsafe_flags(tmp_path):
    path = tmp_path / "relative_strength.yaml"
    path.write_text(
        """
relative_strength:
  paper_trading_only: true
  timing_mode: completed_daily_bar
  disabled_behaviors:
    intrabar_validity: true
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="intrabar_validity"):
        load_relative_strength_config(path)


def test_relative_strength_rejection_reason_vocabulary():
    assert SetupRejectionReason.WEAK_SPY_RELATIVE_STRENGTH in set(SetupRejectionReason)
    assert SetupRejectionReason.EXCESSIVE_52_WEEK_HIGH_DISTANCE in set(SetupRejectionReason)


def test_relative_strength_contract_result_is_setup_only():
    result = contract_result("msft", datetime(2026, 6, 14, tzinfo=timezone.utc))

    assert isinstance(result, SetupResult)
    assert result.status is SetupStatus.REJECTED
    assert result.symbol == "MSFT"
    assert result.timing.timing_mode == "completed_daily_bar"
    assert result.timing.intrabar_valid is False
    assert not hasattr(result, "order")
    assert not hasattr(result, "classification")
    assert not hasattr(result, "total_score")


def test_relative_strength_loader_uses_safe_load():
    text = Path("marketpilot/setups/relative_strength.py").read_text(encoding="utf-8")

    assert "yaml.safe_load" in text
