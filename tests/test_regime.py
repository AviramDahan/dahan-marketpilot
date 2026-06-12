from pathlib import Path

from marketpilot.regime import (
    BenchmarkSnapshot,
    MarketRegime,
    classify_market_regime,
    load_regime_config,
)


def supportive(symbol):
    return BenchmarkSnapshot(symbol, price=110, ema20=105, ema50=100, ema200=90, slope20=1, slope60=1, return20=3, return60=5)


def defensive(symbol):
    return BenchmarkSnapshot(symbol, price=80, ema20=85, ema50=90, ema200=100, slope20=-1, slope60=-1, return20=-3, return60=-5)


def test_regime_config_contains_safety_boundaries():
    config = load_regime_config()

    assert config["benchmark_symbols"] == ["SPY", "QQQ"]
    assert config["entry_gate_only"] is True
    assert config["liquidate_on_risk_off"] is False
    assert config["override_exits"] is False


def test_classifies_risk_on_neutral_and_risk_off():
    risk_on = classify_market_regime([supportive("SPY"), supportive("QQQ")])
    neutral = classify_market_regime([supportive("SPY"), defensive("QQQ")])
    risk_off = classify_market_regime([defensive("SPY"), defensive("QQQ")])

    assert risk_on.regime is MarketRegime.RISK_ON
    assert risk_on.future_entries_allowed is True
    assert neutral.regime is MarketRegime.NEUTRAL
    assert neutral.future_entries_allowed is True
    assert risk_off.regime is MarketRegime.RISK_OFF
    assert risk_off.future_entries_allowed is False


def test_transition_detection_and_unchanged_state_suppression():
    changed = classify_market_regime([supportive("SPY"), supportive("QQQ")], previous_regime=MarketRegime.RISK_OFF)
    unchanged = classify_market_regime([supportive("SPY"), supportive("QQQ")], previous_regime=MarketRegime.RISK_ON)

    assert changed.changed is True
    assert unchanged.changed is False


def test_unready_or_missing_benchmark_blocks_future_entries():
    unready = classify_market_regime([BenchmarkSnapshot("SPY", 110, 105, 100, 90, 1, 1, 3, 5, ready=False), supportive("QQQ")])
    missing = classify_market_regime([supportive("SPY")])

    assert unready.regime is MarketRegime.NEUTRAL
    assert unready.future_entries_allowed is False
    assert "unready_benchmark" in unready.reasons
    assert missing.future_entries_allowed is False
    assert "missing_benchmark" in missing.reasons


def test_regime_source_contains_no_order_or_alert_behavior():
    text = (Path(__file__).resolve().parents[1] / "marketpilot" / "regime.py").read_text(encoding="utf-8")
    forbidden = ["MarketOrder", "SetHoldings", "send_telegram", "Telegram"]

    for value in forbidden:
        assert value not in text

