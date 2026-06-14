from pathlib import Path


SOURCE = Path("marketpilot/order_lifecycle.py").read_text(encoding="utf-8")


def test_order_lifecycle_has_no_quantconnect_or_broker_submission_behavior():
    forbidden = (
        "MarketOrder(",
        "LimitOrder(",
        "StopMarketOrder(",
        ".Submit(",
        ".submit_order(",
        "requests.",
        "telegram_delivery(",
        "broker_adapter",
    )

    for token in forbidden:
        assert token not in SOURCE
