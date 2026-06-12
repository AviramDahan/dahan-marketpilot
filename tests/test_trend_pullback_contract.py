from datetime import datetime, timezone
from pathlib import Path

from marketpilot.setups.base import NumericEvidence, SetupRejectionReason, SetupResult, SetupStatus, SetupTiming
from marketpilot.setups.trend_pullback import contract_result, load_trend_pullback_config


ROOT = Path(__file__).resolve().parents[1]


def test_trend_pullback_config_contains_safety_bounded_defaults():
    config = load_trend_pullback_config()

    assert config["paper_trading_only"] is True
    assert config["timing_mode"] == "completed_daily_bar"
    assert config["min_pullback_bars"] == 2
    assert config["max_pullback_bars"] == 10
    assert config["trend"]["reject_close_below_ema50"] is True
    assert config["disabled_behaviors"]["intrabar_validity"] is False
    assert config["disabled_behaviors"]["create_orders"] is False
    assert config["disabled_behaviors"]["buy_watch_avoid_classifications"] is False


def test_setup_result_contract_supports_valid_rejected_and_evidence():
    timing = SetupTiming(signal_time=datetime(2026, 6, 13, tzinfo=timezone.utc))
    result = SetupResult(
        setup_name="trend_pullback",
        symbol="MSFT",
        status=SetupStatus.VALID,
        timing=timing,
        evidence=(NumericEvidence("ema20_distance_pct", 1.2, 2.5, True),),
    )

    assert result.valid is True
    assert result.timing.uses_completed_daily_bar is True
    assert result.timing.intrabar_valid is False
    assert result.evidence[0].name == "ema20_distance_pct"


def test_rejection_reason_contract_covers_phase_3_hard_rejections():
    required = {
        SetupRejectionReason.RISK_OFF,
        SetupRejectionReason.DATA_NOT_READY,
        SetupRejectionReason.EMA50_BREAK,
        SetupRejectionReason.EXCESSIVE_ATR,
        SetupRejectionReason.WEAK_REWARD_RISK,
        SetupRejectionReason.INCOMPLETE_COMPLETED_BAR_DATA,
        SetupRejectionReason.EARNINGS_SOURCE_UNVERIFIED,
    }

    assert required.issubset(set(SetupRejectionReason))


def test_contract_result_is_not_a_trade_instruction():
    result = contract_result("msft", datetime(2026, 6, 13, tzinfo=timezone.utc))

    assert result.symbol == "MSFT"
    assert result.status is SetupStatus.REJECTED
    assert result.rejection_reasons == (SetupRejectionReason.INCOMPLETE_COMPLETED_BAR_DATA,)
    assert result.timing.timing_mode == "completed_daily_bar"


def test_trend_pullback_modules_contain_no_forbidden_behavior():
    text = (
        (ROOT / "marketpilot" / "setups" / "base.py").read_text(encoding="utf-8")
        + (ROOT / "marketpilot" / "setups" / "trend_pullback.py").read_text(encoding="utf-8")
    )
    forbidden = ["BUY", "WATCH", "AVOID", "MarketOrder", "SetHoldings", "Liquidate", "send_telegram", "BacktestResult"]

    for value in forbidden:
        assert value not in text

