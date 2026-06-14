from pathlib import Path


SOURCES = "\n".join(
    [
        Path("marketpilot/audit_journal.py").read_text(encoding="utf-8"),
        Path("marketpilot/recovery.py").read_text(encoding="utf-8"),
    ]
)


def test_persistence_modules_do_not_create_authoritative_portfolio_or_external_calls():
    forbidden = (
        "MarketOrder(",
        "SetHoldings(",
        "requests.",
        "telegram_delivery(",
        "fake_portfolio_authority = True",
        "quantconnect_wins=False",
    )

    for token in forbidden:
        assert token not in SOURCES
