from datetime import datetime, timezone
from decimal import Decimal

from marketpilot.exits import (
    ExitPlan,
    HoldingPeriodPolicy,
    StopModel,
    TargetModel,
    TrailingStopPolicy,
    evaluate_protective_recovery,
)
from marketpilot.notification_events import (
    NotificationDeduplicator,
    NotificationDomainEvent,
    NotificationRateLimiter,
    notification_delivery_key,
)
from marketpilot.quantconnect_paper import (
    QuantConnectAlgorithmStatus,
    QuantConnectDeploymentStatus,
    QuantConnectHolding,
    QuantConnectPaperFill,
    QuantConnectPaperOrder,
    QuantConnectPaperPerformance,
    QuantConnectPaperSnapshot,
)
from marketpilot.telegram import (
    TelegramConfig,
    TelegramDeliveryService,
    TelegramDeliveryStatus,
    format_telegram_message,
)


class FakeTelegramHttpClient:
    def __init__(self, response=None, error=None):
        self.response = response if response is not None else {"ok": True, "result": {"message_id": 1}}
        self.error = error
        self.calls = []

    def __call__(self, *, url, payload, timeout_seconds):
        self.calls.append({"url": url, "payload": payload, "timeout_seconds": timeout_seconds})
        if self.error is not None:
            raise self.error
        return self.response


def _config():
    return TelegramConfig(
        paper_trading_only=True,
        telegram_enabled=True,
        delivery_required_for_safety=False,
        token_env_var="MP_TELEGRAM_BOT_TOKEN",
        chat_id_env_var="MP_TELEGRAM_CHAT_ID",
        bot_token="fake-token-from-external-store",
        chat_id="fake-chat-from-external-store",
    )


def _exit_plan() -> ExitPlan:
    return ExitPlan(
        symbol="MSFT",
        entry_price=Decimal("421.50"),
        stop=StopModel(price=Decimal("400"), source="test_fixture"),
        target=TargetModel(price=Decimal("465"), r_multiple=Decimal("2")),
        partial_exit_rules=(),
        trailing_stop=TrailingStopPolicy(enabled=False),
        holding_period=HoldingPeriodPolicy(maximum_days=30),
        obligations_active=True,
    )


def _filled_snapshot_without_protection() -> QuantConnectPaperSnapshot:
    return QuantConnectPaperSnapshot(
        fixture_label="deterministic-test-fixture",
        captured_at=datetime(2026, 6, 14, 16, 0, tzinfo=timezone.utc),
        cash=Decimal("95000"),
        portfolio_equity=Decimal("100250"),
        holdings=(
            QuantConnectHolding(symbol="MSFT", quantity=10, average_price=Decimal("421.50"), market_price=Decimal("425")),
        ),
        orders=(
            QuantConnectPaperOrder(
                quantconnect_order_id="qc-entry-1",
                symbol="MSFT",
                status="filled",
                quantity=10,
                submitted_at=datetime(2026, 6, 14, 14, 1, tzinfo=timezone.utc),
                idempotency_key="intent-msft",
            ),
        ),
        fills=(
            QuantConnectPaperFill(
                quantconnect_order_id="qc-entry-1",
                symbol="MSFT",
                quantity=10,
                fill_price=Decimal("421.50"),
                filled_at=datetime(2026, 6, 14, 14, 2, tzinfo=timezone.utc),
            ),
        ),
        deployment_status=QuantConnectDeploymentStatus.RUNNING,
        algorithm_status=QuantConnectAlgorithmStatus.RUNNING,
        performance=QuantConnectPaperPerformance(total_orders=1, total_fills=1, unrealized_profit=Decimal("35")),
    )


def test_telegram_failure_is_observational_for_protective_recovery_decision():
    decision = evaluate_protective_recovery(
        snapshot=_filled_snapshot_without_protection(),
        exit_plans=(_exit_plan(),),
        correlation_id="protective-telegram-1",
    )
    failing_client = FakeTelegramHttpClient(error=TimeoutError("telegram unavailable"))

    delivery = TelegramDeliveryService(_config(), http_client=failing_client).deliver(decision.notification_event)

    assert delivery.status is TelegramDeliveryStatus.FAILED
    assert decision.block_new_entries is True
    assert decision.preserve_exits is True
    assert decision.protective_recovery_required is True
    assert decision.missing_protection_symbols == ("MSFT",)


def test_dedup_uses_event_type_and_correlation_id_before_delivery():
    dedup = NotificationDeduplicator()
    client = FakeTelegramHttpClient()
    service = TelegramDeliveryService(_config(), http_client=client, deduplicator=dedup)
    first = NotificationDomainEvent.create("order_intent", "corr-same", {"symbol": "MSFT"})
    duplicate = NotificationDomainEvent.create("order_intent", "corr-same", {"symbol": "MSFT"})
    different_type = NotificationDomainEvent.create("system", "corr-same", {"system_health": "ok"})

    assert notification_delivery_key(first) == "order_intent|corr-same"
    assert notification_delivery_key(different_type) == "system|corr-same"
    assert service.deliver(first).status is TelegramDeliveryStatus.DELIVERED
    assert service.deliver(duplicate).status is TelegramDeliveryStatus.DUPLICATE_SUPPRESSED
    assert service.deliver(different_type).status is TelegramDeliveryStatus.DELIVERED
    assert len(client.calls) == 2


def test_local_rate_limit_is_delivery_only_and_does_not_raise():
    client = FakeTelegramHttpClient()
    service = TelegramDeliveryService(
        _config(),
        http_client=client,
        rate_limiter=NotificationRateLimiter(max_events=1, window_seconds=60),
    )

    first = service.deliver(NotificationDomainEvent.create("system", "rate-1", {"system_health": "ok"}))
    second = service.deliver(NotificationDomainEvent.create("system", "rate-2", {"system_health": "ok"}))

    assert first.status is TelegramDeliveryStatus.DELIVERED
    assert second.status is TelegramDeliveryStatus.RATE_LIMITED
    assert len(client.calls) == 1


def test_formatted_messages_include_paper_warning_and_remove_unsafe_content():
    event = NotificationDomainEvent.create(
        "order_intent",
        "sanitize-1",
        {
            "symbol": "MSFT",
            "score": 82,
            "paper_trade": True,
            "telegram_chat_id": "must-not-render",
            "reason": "guaranteed profit from setup",
        },
    )

    text = format_telegram_message(event)

    assert "SIMULATED PAPER TRADING ONLY - NOT FINANCIAL ADVICE" in text
    assert "MSFT" in text
    assert "telegram_chat_id" not in text
    assert "must-not-render" not in text
    assert "guaranteed profit" not in text.lower()
    assert "[removed unsafe claim]" in text
