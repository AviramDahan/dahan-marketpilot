from pathlib import Path


RISK_SOURCE = Path("marketpilot/risk.py").read_text(encoding="utf-8")


def test_risk_module_has_no_order_submission_or_external_delivery_behavior():
    forbidden = (
        ".submit_order(",
        "MarketOrder(",
        "LimitOrder(",
        "StopMarketOrder(",
        "requests.",
        "telegram_delivery(",
        "live_deployment = True",
        "fake_portfolio_authority = True",
    )

    for token in forbidden:
        assert token not in RISK_SOURCE
