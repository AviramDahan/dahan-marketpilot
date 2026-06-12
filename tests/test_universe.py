from datetime import datetime, timezone

from marketpilot.data_quality import DataQualityIssue, DataQualityStatus, UniverseCandidate
from marketpilot.universe import build_universe_snapshot, evaluate_candidate, load_universe_config


CONFIG = {
    "paper_trading_only": True,
    "common_equity_only": True,
    "min_price_usd": 5,
    "min_history_bars": 250,
    "min_average_volume_20": 500000,
    "min_average_dollar_volume_20": 20000000,
    "min_market_cap_usd": 1000000000,
}


def valid_candidate(symbol="MSFT", sector="Technology"):
    return UniverseCandidate(
        symbol=symbol,
        price=350,
        history_bars=300,
        average_volume_20=2000000,
        average_dollar_volume_20=700000000,
        market_cap=2500000000000,
        sector=sector,
    )


def test_load_universe_config_contains_required_thresholds():
    config = load_universe_config()

    assert config["min_price_usd"] == 5
    assert config["min_history_bars"] == 250
    assert config["min_average_volume_20"] == 500000
    assert config["min_average_dollar_volume_20"] == 20000000
    assert config["min_market_cap_usd"] == 1000000000
    assert config["exclusions"]["etf"] is True
    assert config["exclusions"]["adr"] is True
    assert config["exclusions"]["otc"] is True
    assert config["exclusions"]["preferred_share"] is True
    assert config["exclusions"]["warrant"] is True


def test_accepts_valid_common_equity_candidate():
    decision = evaluate_candidate(valid_candidate(), CONFIG)

    assert decision.status is DataQualityStatus.ACCEPTED
    assert decision.issues == ()


def test_rejects_price_history_volume_and_dollar_volume_failures():
    candidate = UniverseCandidate(
        symbol="LOWQ",
        price=4.99,
        history_bars=249,
        average_volume_20=499999,
        average_dollar_volume_20=19999999,
        market_cap=999999999,
    )

    decision = evaluate_candidate(candidate, CONFIG)

    assert decision.status is DataQualityStatus.REJECTED
    assert DataQualityIssue.BELOW_MIN_PRICE in decision.issues
    assert DataQualityIssue.INSUFFICIENT_HISTORY in decision.issues
    assert DataQualityIssue.BELOW_MIN_VOLUME in decision.issues
    assert DataQualityIssue.BELOW_MIN_DOLLAR_VOLUME in decision.issues
    assert DataQualityIssue.BELOW_MIN_MARKET_CAP in decision.issues


def test_rejects_stale_etf_adr_otc_preferred_warrant_and_missing_data():
    candidates = [
        UniverseCandidate("ETF", 100, 300, 1000000, 100000000, is_etf=True),
        UniverseCandidate("ADR", 100, 300, 1000000, 100000000, is_adr=True),
        UniverseCandidate("OTC", 100, 300, 1000000, 100000000, is_otc=True),
        UniverseCandidate("PREF", 100, 300, 1000000, 100000000, is_preferred_share=True),
        UniverseCandidate("WRT", 100, 300, 1000000, 100000000, is_warrant=True),
        UniverseCandidate("OLD", 100, 300, 1000000, 100000000, is_stale=True),
        UniverseCandidate("MISS", None, 300, 1000000, 100000000, missing_fields=("price",)),
    ]

    issues = [evaluate_candidate(candidate, CONFIG).issues[0] for candidate in candidates]

    assert issues == [
        DataQualityIssue.ETF_EXCLUDED,
        DataQualityIssue.ADR_EXCLUDED,
        DataQualityIssue.OTC_EXCLUDED,
        DataQualityIssue.PREFERRED_EXCLUDED,
        DataQualityIssue.WARRANT_EXCLUDED,
        DataQualityIssue.STALE_DATA,
        DataQualityIssue.CRITICAL_MISSING_DATA,
    ]


def test_snapshot_tracks_counts_additions_removals_reasons_and_sectors():
    snapshot = build_universe_snapshot(
        [
            valid_candidate("MSFT", "Technology"),
            valid_candidate("JPM", "Financials"),
            UniverseCandidate("BAD", 2, 300, 1000000, 100000000),
        ],
        CONFIG,
        previous_accepted={"AAPL", "MSFT"},
        update_time=datetime(2026, 6, 13, tzinfo=timezone.utc),
    )

    assert snapshot.accepted_symbols == ("MSFT", "JPM")
    assert snapshot.rejected_symbols == ("BAD",)
    assert snapshot.accepted_count == 2
    assert snapshot.rejected_count == 1
    assert snapshot.additions == ("JPM",)
    assert snapshot.removals == ("AAPL",)
    assert snapshot.sector_distribution == {"Technology": 1, "Financials": 1}
    assert snapshot.decisions[2].issues == (DataQualityIssue.BELOW_MIN_PRICE,)


def test_snapshot_does_not_silently_truncate_to_tiny_list():
    snapshot = build_universe_snapshot(
        [valid_candidate("AAA"), UniverseCandidate("BBB", 1, 300, 1000000, 100000000)],
        CONFIG,
    )

    assert snapshot.accepted_count == 1
    assert snapshot.rejected_count == 1
    assert snapshot.decisions[1].issues

