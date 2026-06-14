from pathlib import Path


SOURCE = Path("marketpilot/exits.py").read_text(encoding="utf-8")


def test_exit_module_has_no_order_or_notification_execution_behavior():
    forbidden = (
        "MarketOrder(",
        "StopMarketOrder(",
        "LimitOrder(",
        ".submit_order(",
        ".cancel_order(",
        "requests.",
        "telegram_delivery(",
    )

    for token in forbidden:
        assert token not in SOURCE
