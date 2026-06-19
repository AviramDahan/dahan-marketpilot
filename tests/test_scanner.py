from datetime import datetime, timezone

from marketpilot.runtime_orchestrator import RuntimeSetupMetadata
from marketpilot.scanner import run_scanner
from marketpilot.setups.base import NumericEvidence, SetupResult, SetupStatus, SetupTiming
from marketpilot.timeframes import StrategyMode
from marketpilot.universe_sources import UniverseSourceRow, build_simulation_universe_snapshot


CONFIG = {
    "paper_trading_only": True,
    "common_equity_only": True,
    "min_price_usd": 5,
    "min_history_bars": 250,
    "min_average_volume_20": 500000,
    "min_average_dollar_volume_20": 20000000,
    "min_market_cap_usd": 1000000000,
}

SIGNAL_TIME = datetime(2026, 6, 19, 20, 0, tzinfo=timezone.utc)


def _row(symbol: str, price=100) -> UniverseSourceRow:
    return UniverseSourceRow(
        symbol=symbol,
        source="test",
        sector="Technology",
        price=price,
        history_bars=300,
        average_volume_20=1000000,
        average_dollar_volume_20=100000000,
        market_cap=10000000000,
    )


def _setup(symbol: str, setup_name: str, valid=True) -> SetupResult:
    return SetupResult(
        setup_name=setup_name,
        symbol=symbol,
        status=SetupStatus.VALID if valid else SetupStatus.REJECTED,
        timing=SetupTiming(signal_time=SIGNAL_TIME, strategy_mode=StrategyMode.DAILY_ONLY),
        evidence=(
            NumericEvidence("close_above_ema50", True, True, True),
            NumericEvidence("ema50_above_ema200", True, True, True),
            NumericEvidence("spy_rs20", 0.05, "> 0", True),
            NumericEvidence("spy_rs60", 0.08, "> 0", True),
            NumericEvidence("rsi14", 58, "supporting", True),
            NumericEvidence("breakout_close", 100, 99, True),
            NumericEvidence("volume_ratio", 2.0, 1.5, True),
            NumericEvidence("reward_risk_proxy", 2.5, 2.0, True),
            NumericEvidence("atr_pct", 4.0, 8.0, True),
            NumericEvidence("regime", "risk_on", "entry_allowed", True),
            NumericEvidence("planned_entry_price", 100, "later_valid_price", True),
            NumericEvidence("initial_stop_price", 95, "risk_model", True),
            NumericEvidence("target_price", 112.5, "risk_model", True),
            NumericEvidence("sector", "Technology", "classification_source", True),
        ),
        explanation=("fixture setup",),
    )


def _registry(calls: list[object]):
    def evaluator(payload):
        calls.append(payload)
        symbol, setup_name, valid = payload
        return _setup(symbol, setup_name, valid=valid)

    return {
        "trend_pullback": RuntimeSetupMetadata("trend_pullback", evaluator, tuple),
        "volume_breakout": RuntimeSetupMetadata("volume_breakout", evaluator, tuple),
        "relative_strength_leader": RuntimeSetupMetadata("relative_strength_leader", evaluator, tuple),
    }


def test_scanner_invokes_existing_registry_for_all_eligible_symbols():
    calls = []
    universe = build_simulation_universe_snapshot([_row("MSFT")], universe_config=CONFIG)
    setup_inputs = {
        ("MSFT", "trend_pullback"): ("MSFT", "trend_pullback", True),
        ("MSFT", "volume_breakout"): ("MSFT", "volume_breakout", True),
        ("MSFT", "relative_strength_leader"): ("MSFT", "relative_strength_leader", True),
    }

    result = run_scanner(
        correlation_id="scan-1",
        universe_snapshot=universe,
        setup_inputs=setup_inputs,
        registry=_registry(calls),
        scanned_at=SIGNAL_TIME,
    )

    assert len(calls) == 3
    assert result.correlation_id == "scan-1"
    assert result.product_mode == "simulation_only"
    assert result.accepted_candidates
    assert result.ranked_candidates[0].symbol == "MSFT"
    assert result.evidence["executes_orders"] is False


def test_rejected_universe_symbol_does_not_reach_setup_evaluation():
    calls = []
    universe = build_simulation_universe_snapshot([_row("LOWQ", price=2)], universe_config=CONFIG)

    result = run_scanner(
        correlation_id="scan-2",
        universe_snapshot=universe,
        setup_inputs={},
        registry=_registry(calls),
        scanned_at=SIGNAL_TIME,
    )

    assert calls == []
    assert result.accepted_candidates == ()
    assert result.rejected_candidates[0].symbol == "LOWQ"
    assert "below_min_price" in result.rejected_candidates[0].reasons


def test_missing_setup_input_and_rejected_setup_remain_visible():
    calls = []
    universe = build_simulation_universe_snapshot([_row("MSFT")], universe_config=CONFIG)
    setup_inputs = {
        ("MSFT", "trend_pullback"): ("MSFT", "trend_pullback", False),
    }

    result = run_scanner(
        correlation_id="scan-3",
        universe_snapshot=universe,
        setup_inputs=setup_inputs,
        registry=_registry(calls),
        scanned_at=SIGNAL_TIME,
    )

    reasons = [reason for rejected in result.rejected_candidates for reason in rejected.reasons]
    assert "setup_rejected" in reasons
    assert "setup_input_missing" in reasons

