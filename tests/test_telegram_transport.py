from datetime import datetime, timezone
from io import BytesIO
from unittest.mock import patch
from urllib.error import HTTPError

from marketpilot.notification_events import NotificationDomainEvent, NotificationRateLimiter
from marketpilot.telegram import (
    TelegramConfig,
    TelegramDeliveryService,
    TelegramDeliveryStatus,
    _post_json,
)


class FakeTelegramHttpClient:
    def __init__(self, response=None, error=None):
        self.response = response if response is not None else {"ok": True, "result": {"message_id": 10}}
        self.error = error
        self.calls = []

    def __call__(self, *, url, payload, timeout_seconds):
        self.calls.append({"url": url, "payload": payload, "timeout_seconds": timeout_seconds})
        if self.error is not None:
            raise self.error
        return self.response


def _event(event_type="order_intent", correlation_id="corr-1", payload=None):
    return NotificationDomainEvent.create(
        event_type,
        correlation_id,
        payload
        or {
            "symbol": "MSFT",
            "setup": "volume_breakout",
            "classification": "BUY_CANDIDATE",
            "score": 82,
            "mode": "limited_paper",
            "paper_trade": True,
            "bot_token": "should-redact",
        },
        severity="info",
        timestamp=datetime(2026, 6, 14, tzinfo=timezone.utc),
    )


def _config(**overrides):
    values = {
        "paper_trading_only": True,
        "telegram_enabled": True,
        "delivery_required_for_safety": False,
        "token_env_var": "MP_TELEGRAM_BOT_TOKEN",
        "chat_id_env_var": "MP_TELEGRAM_CHAT_ID",
        "bot_token": "fake-token-from-external-store",
        "chat_id": "fake-chat-from-external-store",
    }
    values.update(overrides)
    return TelegramConfig(**values)


def test_disabled_missing_secret_and_rate_limited_results_do_not_call_http():
    event = _event()
    client = FakeTelegramHttpClient()

    disabled = TelegramDeliveryService(_config(telegram_enabled=False), http_client=client).deliver(event)
    missing_token = TelegramDeliveryService(_config(bot_token=None), http_client=client).deliver(event)
    missing_chat = TelegramDeliveryService(_config(chat_id=None), http_client=client).deliver(event)
    rate_limited = TelegramDeliveryService(
        _config(),
        http_client=client,
        rate_limiter=NotificationRateLimiter(max_events=0, window_seconds=60),
    ).deliver(event)

    assert disabled.status is TelegramDeliveryStatus.DISABLED
    assert missing_token.status is TelegramDeliveryStatus.MISSING_TOKEN
    assert missing_chat.status is TelegramDeliveryStatus.MISSING_CHAT_ID
    assert rate_limited.status is TelegramDeliveryStatus.RATE_LIMITED
    assert client.calls == []


def test_delivered_result_posts_plain_text_send_message_payload():
    client = FakeTelegramHttpClient({"ok": True, "result": {"message_id": 42}})
    result = TelegramDeliveryService(_config(), http_client=client).deliver(_event())

    assert result.status is TelegramDeliveryStatus.DELIVERED
    assert result.telegram_message_id == "42"
    assert len(client.calls) == 1
    call = client.calls[0]
    assert call["url"].endswith("/sendMessage")
    assert call["payload"]["chat_id"] == "fake-chat-from-external-store"
    assert "SIMULATED PAPER TRADING ONLY - NOT FINANCIAL ADVICE" in call["payload"]["text"]
    assert "MSFT" in call["payload"]["text"]
    assert "fake-token-from-external-store" not in call["payload"]["text"]
    assert "bot_token" not in call["payload"]["text"]
    assert "parse_mode" not in call["payload"]
    assert "allow_paid_broadcast" not in call["payload"]


def test_api_rejection_and_quota_response_map_to_typed_results_without_secret_leakage():
    rejected_client = FakeTelegramHttpClient({"ok": False, "error_code": 400, "description": "Bad Request"})
    rejected = TelegramDeliveryService(_config(), http_client=rejected_client).deliver(_event())

    quota_client = FakeTelegramHttpClient(
        {"ok": False, "error_code": 429, "description": "Too Many Requests", "parameters": {"retry_after": 17}}
    )
    quota = TelegramDeliveryService(_config(), http_client=quota_client).deliver(_event("system", "corr-429"))

    assert rejected.status is TelegramDeliveryStatus.REJECTED
    assert rejected.error_code == 400
    assert quota.status is TelegramDeliveryStatus.RATE_LIMITED
    assert quota.retry_after_seconds == 17
    assert "fake-token-from-external-store" not in repr(rejected)
    assert "fake-token-from-external-store" not in repr(quota)


def test_network_exception_maps_to_failed_result_without_raising():
    client = FakeTelegramHttpClient(error=TimeoutError("socket timed out"))

    result = TelegramDeliveryService(_config(), http_client=client).deliver(_event())

    assert result.status is TelegramDeliveryStatus.FAILED
    assert result.detail == "socket timed out"


def test_http_error_body_is_returned_as_telegram_rejection_payload():
    error = HTTPError(
        url="https://api.telegram.org/bot[redacted]/sendMessage",
        code=400,
        msg="Bad Request",
        hdrs=None,
        fp=BytesIO(b'{"ok":false,"error_code":400,"description":"Bad Request: chat not found"}'),
    )

    with patch("marketpilot.telegram.urllib.request.urlopen", side_effect=error):
        response = _post_json(
            url="https://api.telegram.org/botfake/sendMessage",
            payload={"chat_id": "bad", "text": "hello"},
            timeout_seconds=1,
        )

    assert response == {"ok": False, "error_code": 400, "description": "Bad Request: chat not found"}
