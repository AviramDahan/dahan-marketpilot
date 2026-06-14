from pathlib import Path


SOURCE = Path("marketpilot/notification_events.py").read_text(encoding="utf-8")


def test_notification_events_have_no_real_telegram_or_network_delivery():
    forbidden = (
        "requests.",
        "httpx.",
        "Bot(",
        "send_message(",
        "chat_id =",
        "telegram_token =",
        "MarketOrder(",
        ".submit_order(",
    )

    for token in forbidden:
        assert token not in SOURCE
