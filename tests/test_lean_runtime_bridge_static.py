from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from marketpilot.data_quality import DataQualityStatus
from marketpilot.indicators import IndicatorResult, ReadinessStatus
from marketpilot.regime import BenchmarkSnapshot, MarketRegime, RegimeResult
from marketpilot.setups.base import NumericEvidence, SetupResult, SetupStatus, SetupTiming
from marketpilot.symbol_data import SymbolData, SymbolLifecycleState
from marketpilot.timeframes import BarCompletionStatus, BarTimeframe, StrategyMode


ROOT = Path(__file__).resolve().parents[1]
LEAN_MAIN = ROOT / "lean" / "main.py"
LEAN_BRIDGE = ROOT / "marketpilot" / "lean_bridge.py"


FORBIDDEN_SAFETY_TOKENS = (
    "SetBrokerageModel",
    "set_brokerage_model",
    "InteractiveBrokers",
    "live_money",
    "real_money",
    "margin",
    "leverage",
    "short",
    "AddOption",
    "add_option",
    "AddFuture",
    "add_future",
    "AddCrypto",
    "add_crypto",
    "AddForex",
    "add_forex",
    "MarketOrder",
    "SetHoldings",
    "set_holdings",
    "Liquidate",
    "liquidate",
    "api_key",
    "token",
    "password",
)


def _fake_bar(**overrides):
    defaults = {
        "EndTime": datetime(2026, 6, 15, 20, 0, tzinfo=timezone.utc),
        "Open": 100.0,
        "High": 105.0,
        "Low": 99.0,
        "Close": 104.0,
        "Volume": 1_500_000,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _ready_symbol_data(symbol: str = "MSFT") -> SymbolData:
    return SymbolData(
        symbol=symbol,
        sector="Technology",
        data_quality_status=DataQualityStatus.ACCEPTED,
        indicators={
            "EMA20": IndicatorResult("EMA20", ReadinessStatus.READY, 101.0, 20, 260),
            "EMA50": IndicatorResult("EMA50", ReadinessStatus.READY, 98.0, 50, 260),
        },
    )


def _benchmarks() -> tuple[BenchmarkSnapshot, ...]:
    return (
        BenchmarkSnapshot("SPY", 500.0, 490.0, 480.0, 450.0, 0.1, 0.2, 2.0, 4.0),
        BenchmarkSnapshot("QQQ", 430.0, 420.0, 410.0, 390.0, 0.1, 0.2, 3.0, 5.0),
    )


def _setup_result() -> SetupResult:
    signal_time = datetime(2026, 6, 15, 20, 0, tzinfo=timezone.utc)
    return SetupResult(
        setup_name="relative_strength_leader",
        symbol="MSFT",
        status=SetupStatus.VALID,
        timing=SetupTiming(signal_time=signal_time, bar_end=signal_time),
        evidence=(
            NumericEvidence("close_above_ema50", True, True, True),
            NumericEvidence("ema50_above_ema200", True, True, True),
            NumericEvidence("spy_rs20", 0.04, "> 0", True),
            NumericEvidence("spy_rs60", 0.06, "> 0", True),
            NumericEvidence("reward_risk_proxy", 2.5, 2.0, True),
            NumericEvidence("planned_entry_price", 104.5, "later_valid_price", True),
            NumericEvidence("initial_stop_price", 99.0, "risk_model", True),
            NumericEvidence("target_price", 116.0, "risk_model", True),
            NumericEvidence("sector", "Technology", "classification_source", True),
        ),
    )


def test_lean_main_uses_only_approved_bridge_lifecycle_hooks():
    text = LEAN_MAIN.read_text(encoding="utf-8")

    assert "from marketpilot.lean_bridge import" in text
    assert "initialize_runtime_bridge" in text
    assert "select_dynamic_universe" in text
    assert "on_securities_changed" in text
    assert "on_completed_daily_bar" in text
    assert "on_completed_bar" in text
    assert "export_dashboard_evidence" in text


def test_runtime_bridge_static_policy_requires_full_runtime_path_tokens():
    combined = LEAN_MAIN.read_text(encoding="utf-8") + "\n" + LEAN_BRIDGE.read_text(encoding="utf-8")

    required_tokens = (
        "dynamic_universe",
        "readiness",
        "map_quantconnect_bar_to_completed_bar",
        "classify_market_regime",
        "IndicatorResult",
        "get_default_setup_registry",
        "run_runtime_pipeline",
        "ranked_candidates",
        "risk_decisions",
        "reconciliation",
        "paper_order_eligible",
        "notification_events",
        "dashboard_export",
        "not_run",
    )
    for token in required_tokens:
        assert token in combined


def test_bridge_and_lean_sources_keep_real_money_and_uncontrolled_order_tokens_forbidden():
    combined = LEAN_MAIN.read_text(encoding="utf-8") + "\n" + LEAN_BRIDGE.read_text(encoding="utf-8")

    for token in FORBIDDEN_SAFETY_TOKENS:
        assert token not in combined

    lean_text = LEAN_MAIN.read_text(encoding="utf-8")
    bridge_text = LEAN_BRIDGE.read_text(encoding="utf-8")
    assert "market_order(" not in bridge_text
    assert lean_text.count("market_order(") == 1
    assert "def on_command" in lean_text
    assert "tag=validation.tag" in lean_text


def test_completed_quantconnect_like_bar_maps_to_signal_valid_completed_bar():
    from marketpilot.lean_bridge import map_quantconnect_bar_to_completed_bar

    completed = map_quantconnect_bar_to_completed_bar(
        _fake_bar(),
        timeframe=BarTimeframe.DAILY,
        exchange_timezone="America/New_York",
        source_resolution="daily",
        is_closed=True,
    )

    assert completed.time == datetime(2026, 6, 15, 20, 0, tzinfo=timezone.utc)
    assert completed.close == 104.0
    assert completed.timeframe is BarTimeframe.DAILY
    assert completed.completion_status is BarCompletionStatus.COMPLETE
    assert completed.session.exchange_timezone == "America/New_York"
    assert completed.session.source_resolution == "daily"
    assert completed.valid_for_signal() is True


@pytest.mark.parametrize(
    "kwargs,expected",
    [
        ({"is_closed": False}, BarCompletionStatus.INCOMPLETE),
        ({"partial_session": True}, BarCompletionStatus.PARTIAL_SESSION),
    ],
)
def test_incomplete_or_partial_bars_are_not_signal_valid(kwargs, expected):
    from marketpilot.lean_bridge import map_quantconnect_bar_to_completed_bar

    completed = map_quantconnect_bar_to_completed_bar(_fake_bar(), timeframe=BarTimeframe.DAILY, **kwargs)

    assert completed.completion_status is expected
    assert completed.valid_for_signal() is False


def test_removed_securities_route_to_symbol_data_cleanup():
    from marketpilot.lean_bridge import LeanRuntimeBridge

    bridge = LeanRuntimeBridge()
    bridge.symbol_data["MSFT"] = _ready_symbol_data()

    removed = bridge.on_securities_changed(SimpleNamespace(RemovedSecurities=[SimpleNamespace(Symbol="MSFT")]))

    assert removed == ("MSFT",)
    assert bridge.symbol_data["MSFT"].lifecycle_state is SymbolLifecycleState.REMOVED
    assert bridge.symbol_data["MSFT"].cleanup_complete is True


def test_missing_benchmark_regime_or_indicator_data_fails_closed():
    from marketpilot.lean_bridge import LeanRuntimeBridge, map_quantconnect_bar_to_completed_bar

    bridge = LeanRuntimeBridge()
    bar = map_quantconnect_bar_to_completed_bar(_fake_bar())

    result = bridge.on_completed_bar(
        symbol="MSFT",
        bar=bar,
        symbol_data=SymbolData("MSFT", "Technology", DataQualityStatus.ACCEPTED),
        benchmark_snapshots=(),
        setup_results=(_setup_result(),),
        required_indicators=("EMA20", "EMA50"),
        correlation_id="lean-missing-data",
    )

    assert result.status.value == "not_ready"
    assert result.evidence["readiness"] == "blocked"
    assert "missing_benchmark_regime" in result.evidence["readiness_reasons"]
    assert "missing_indicator_readiness" in result.evidence["readiness_reasons"]
    assert result.evidence["executes_orders"] is False


def test_completed_bar_bridge_builds_runtime_input_without_strategy_logic_in_lean_main():
    from marketpilot.lean_bridge import LeanRuntimeBridge, map_quantconnect_bar_to_completed_bar

    bridge = LeanRuntimeBridge()
    bar = map_quantconnect_bar_to_completed_bar(_fake_bar())
    result = bridge.on_completed_bar(
        symbol="MSFT",
        bar=bar,
        symbol_data=_ready_symbol_data(),
        benchmark_snapshots=_benchmarks(),
        regime_result=RegimeResult(MarketRegime.RISK_ON, True, False, None, ("benchmarks_supportive",)),
        setup_results=(_setup_result(),),
        required_indicators=("EMA20", "EMA50"),
        correlation_id="lean-runtime-input",
        strategy_mode=StrategyMode.DAILY_ONLY,
    )

    assert result.correlation_id == "lean-runtime-input"
    assert result.evidence["completed_bar_adapter"] == "quantconnect_like"
    assert result.evidence["setup_registry"] == (
        "relative_strength_leader",
        "trend_pullback",
        "volume_breakout",
    )
    assert result.evidence["scoring_ranking"] == "runtime_orchestrator"
    assert result.evidence["risk"] == "runtime_orchestrator"
    assert result.evidence["reconciliation"] == "runtime_orchestrator"
    assert result.evidence["paper_eligibility"] == "runtime_orchestrator"
    assert result.evidence["notification_events"] == "runtime_orchestrator"
    assert result.evidence["dashboard_export"]["status"] == "not_run"
    assert result.order_intents == ()
