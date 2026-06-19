from marketpilot.universe_sources import (
    UniverseSourceRow,
    build_simulation_universe_snapshot,
    decision_reason_map,
    dedupe_universe_rows,
    load_universe_source_rows,
)


CONFIG = {
    "paper_trading_only": True,
    "common_equity_only": True,
    "min_price_usd": 5,
    "min_history_bars": 250,
    "min_average_volume_20": 500000,
    "min_average_dollar_volume_20": 20000000,
    "min_market_cap_usd": 1000000000,
}


def _row(symbol: str, **overrides) -> UniverseSourceRow:
    data = {
        "symbol": symbol,
        "source": "test",
        "price": 100,
        "history_bars": 300,
        "average_volume_20": 1000000,
        "average_dollar_volume_20": 100000000,
        "market_cap": 10000000000,
        "sector": "Technology",
    }
    data.update(overrides)
    return UniverseSourceRow(**data)


def test_load_universe_source_rows_from_default_config_is_deterministic():
    rows = load_universe_source_rows()

    assert tuple(row.symbol for row in rows) == ("AAPL", "MSFT", "NVDA", "JPM", "UNH")
    assert all(row.normalized_symbol == row.symbol for row in rows)


def test_dedupe_preserves_first_symbol_order_and_reports_duplicates():
    rows, duplicates = dedupe_universe_rows([_row("msft"), _row("AAPL"), _row("MSFT")])

    assert tuple(row.normalized_symbol for row in rows) == ("MSFT", "AAPL")
    assert duplicates == ("MSFT",)


def test_build_simulation_universe_snapshot_records_acceptance_and_rejection_reasons():
    snapshot = build_simulation_universe_snapshot(
        [_row("MSFT"), _row("LOWQ", price=2)],
        universe_config=CONFIG,
    )

    assert snapshot.product_mode == "simulation_only"
    assert snapshot.accepted_symbols == ("MSFT",)
    assert snapshot.rejected_symbols == ("LOWQ",)
    assert decision_reason_map(snapshot)["LOWQ"] == ("below_min_price",)


def test_missing_liquidity_data_fails_closed_with_reasons():
    snapshot = build_simulation_universe_snapshot(
        [_row("NODATA", average_volume_20=None, average_dollar_volume_20=None)],
        universe_config=CONFIG,
    )

    reasons = decision_reason_map(snapshot)["NODATA"]
    assert "critical_missing_data" in reasons

