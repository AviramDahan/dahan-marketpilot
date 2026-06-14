from datetime import datetime, timezone

from marketpilot.notification_events import event_for_alert_family, event_for_protective_recovery
from marketpilot.telegram import (
    TelegramConfig,
    TelegramDeliveryService,
    TelegramDeliveryStatus,
)


class FakeTelegramHttpClient:
    def __init__(self, response=None, error=None):
        self.response = response if response is not None else {"ok": False, "error_code": 400, "description": "Bad Request"}
        self.error = error
        self.calls = []

    def __call__(self, *, url, payload, timeout_seconds):
        self.calls.append({"url": url, "payload": payload, "timeout_seconds": timeout_seconds})
        if self.error is not None:
            raise self.error
        return self.response


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


def test_failure_results_are_typed_and_non_authoritative_for_representative_alerts():
    service = TelegramDeliveryService(_config(), http_client=FakeTelegramHttpClient(error=TimeoutError("offline")))
    events = (
        event_for_alert_family("buy_candidate", "signal-1", {"symbol": "MSFT"}),
        event_for_alert_family("submitted_order", "order-1", {"symbol": "MSFT", "order_state": "submitted"}),
        event_for_alert_family("partial_fill", "fill-1", {"symbol": "MSFT", "fill_state": "partial"}),
        event_for_protective_recovery("protective-1", {"symbol": "MSFT", "block_new_entries": True}),
        event_for_alert_family("regime_change", "regime-1", {"regime_state": "RISK_OFF"}),
        event_for_alert_family("system", "system-1", {"system_health": "degraded"}),
        event_for_alert_family("error", "error-1", {"reason": "telegram offline"}),
        event_for_alert_family("start_restart", "restart-1", {"system_health": "restarted"}),
        event_for_alert_family("daily_summary", "summary-1", {"active_paper_mode": "limited_paper"}),
    )

    results = [service.deliver(event) for event in events]

    assert {result.status for result in results} == {TelegramDeliveryStatus.FAILED}
    assert all(result.to_safe_dict()["controls_safety_logic"] is False for result in results)
    assert all(result.to_safe_dict()["delivery_required_for_safety"] is False for result in results)


def test_disabled_missing_secret_quota_and_rejection_statuses_are_non_authoritative():
    event = event_for_alert_family("paper_buy", "paper-buy-1", {"symbol": "MSFT"})

    disabled = TelegramDeliveryService(_config(telegram_enabled=False)).deliver(event)
    missing_token = TelegramDeliveryService(_config(bot_token=None)).deliver(event)
    missing_chat = TelegramDeliveryService(_config(chat_id=None)).deliver(event)
    rejected = TelegramDeliveryService(
        _config(),
        http_client=FakeTelegramHttpClient({"ok": False, "error_code": 400, "description": "Bad Request"}),
    ).deliver(event)
    quota = TelegramDeliveryService(
        _config(),
        http_client=FakeTelegramHttpClient(
            {"ok": False, "error_code": 429, "description": "Too Many Requests", "parameters": {"retry_after": 30}}
        ),
    ).deliver(event)

    assert disabled.status is TelegramDeliveryStatus.DISABLED
    assert missing_token.status is TelegramDeliveryStatus.MISSING_TOKEN
    assert missing_chat.status is TelegramDeliveryStatus.MISSING_CHAT_ID
    assert rejected.status is TelegramDeliveryStatus.REJECTED
    assert quota.status is TelegramDeliveryStatus.RATE_LIMITED
    assert all(
        result.to_safe_dict()["controls_safety_logic"] is False
        for result in (disabled, missing_token, missing_chat, rejected, quota)
    )


def test_telegram_failure_does_not_mutate_external_safety_decisions():
    safety_decision = {
        "paper_mode": "limited_paper",
        "order_lifecycle_state": "submitted",
        "protective_exit_required": True,
        "reconciliation_block_new_entries": True,
        "daily_summary_created": True,
    }
    before = dict(safety_decision)
    service = TelegramDeliveryService(_config(), http_client=FakeTelegramHttpClient(error=ConnectionError("offline")))

    result = service.deliver(
        event_for_alert_family(
            "daily_summary",
            "summary-failure-isolation",
            {"active_paper_mode": "limited_paper", "system_health": "degraded"},
            timestamp=datetime(2026, 6, 14, tzinfo=timezone.utc),
        )
    )

    assert result.status is TelegramDeliveryStatus.FAILED
    assert safety_decision == before
