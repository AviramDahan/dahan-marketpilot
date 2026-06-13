from datetime import datetime, timezone

from marketpilot.data_quality import DataQualityStatus
from marketpilot.indicators import IndicatorResult, ReadinessStatus
from marketpilot.regime import MarketRegime, RegimeResult
from marketpilot.setups.base import SetupStatus
from marketpilot.setups.relative_strength import CompletedDailyBar, RelativeStrengthInput, evaluate_relative_strength_leader
from marketpilot.symbol_data import SymbolData


def ready_indicator(name, value):
    return IndicatorResult(name=name, status=ReadinessStatus.READY, value=value, required_points=20, available_points=260)


def indicators():
    return {
        "EMA20": ready_indicator("EMA20", 100.0),
        "EMA50": ready_indicator("EMA50", 98.0),
        "EMA200": ready_indicator("EMA200", 80.0),
        "ATR14": ready_indicator("ATR14", 4.0),
    }


def bars():
    return tuple(
        CompletedDailyBar(
            time=datetime(2026, 1, 1, tzinfo=timezone.utc),
            open=100 + index * 0.1,
            high=101 + index * 0.1,
            low=99 + index * 0.1,
            close=100 + index * 0.1,
            volume=1000000,
        )
        for index in range(70)
    )


def valid_input(**overrides):
    active = indicators()
    setup_input = RelativeStrengthInput(
        symbol_data=SymbolData("MSFT", "Technology", DataQualityStatus.ACCEPTED, active),
        regime=RegimeResult(MarketRegime.RISK_ON, True, True, None, ("supportive",)),
        bars=bars(),
        indicators=active,
        symbol_returns=[0.03] * 70,
        spy_returns=[0.01] * 70,
        qqq_returns=[-0.02] * 70,
        average_dollar_volume=30000000,
        atr_pct=4.0,
        ema20_extension_pct=5.0,
    )
    return RelativeStrengthInput(**{**setup_input.__dict__, **overrides})


def evidence_value(result, name):
    return next(item.value for item in result.evidence if item.name == name)


def test_detects_valid_relative_strength_leader_with_qqq_evidence_only():
    result = evaluate_relative_strength_leader(valid_input())

    assert result.status is SetupStatus.VALID
    assert result.rejection_reasons == ()
    assert evidence_value(result, "spy_rs20") > 0
    assert evidence_value(result, "spy_rs60") > 0
    assert evidence_value(result, "qqq_rs20") > 0
    assert result.timing.timing_mode == "completed_daily_bar"


def test_weak_qqq_alone_does_not_reject():
    result = evaluate_relative_strength_leader(valid_input(qqq_returns=[0.05] * 70))

    assert result.status is SetupStatus.VALID
    assert evidence_value(result, "qqq_rs20") < 0
