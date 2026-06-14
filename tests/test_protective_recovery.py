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
from marketpilot.notification_events import FakeNotificationCollector, NotificationEventType
from marketpilot.quantconnect_paper import (
    QuantConnectAlgorithmStatus,
    QuantConnectDeploymentStatus,
    QuantConnectHolding,
    QuantConnectPaperFill,
    QuantConnectPaperOrder,
    QuantConnectPaperPerformance,
    QuantConnectPaperSnapshot,
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


def test_filled_paper_position_without_protective_state_blocks_new_entries():
    decision = evaluate_protective_recovery(
        snapshot=_filled_snapshot_without_protection(),
        exit_plans=(_exit_plan(),),
        correlation_id="protective-1",
    )

    assert decision.block_new_entries is True
    assert decision.preserve_exits is True
    assert decision.protective_recovery_required is True
    assert decision.missing_protection_symbols == ("MSFT",)
    assert decision.notification_event is not None
    assert decision.notification_event.event_type == NotificationEventType.PROTECTIVE_RECOVERY.value
    assert decision.notification_event.severity == "high"


def test_protective_recovery_event_is_sanitized_and_delivery_failure_is_non_authoritative():
    collector = FakeNotificationCollector(fail_delivery=True)

    decision = evaluate_protective_recovery(
        snapshot=_filled_snapshot_without_protection(),
        exit_plans=(_exit_plan(),),
        correlation_id="protective-2",
        notification_collector=collector,
    )

    assert decision.protective_recovery_required is True
    assert decision.notification_delivery_attempted is True
    assert decision.notification_delivery_succeeded is False
    assert decision.block_new_entries is True
    assert collector.failures == [NotificationEventType.PROTECTIVE_RECOVERY.value]
    assert "token" not in str(decision.notification_event.payload).lower()


def test_protective_exit_logic_continues_when_fake_notification_collector_fails():
    failing_collector = FakeNotificationCollector(fail_delivery=True)

    with_failure = evaluate_protective_recovery(
        snapshot=_filled_snapshot_without_protection(),
        exit_plans=(_exit_plan(),),
        correlation_id="protective-3",
        notification_collector=failing_collector,
    )
    without_delivery = evaluate_protective_recovery(
        snapshot=_filled_snapshot_without_protection(),
        exit_plans=(_exit_plan(),),
        correlation_id="protective-3",
    )

    assert with_failure.protective_recovery_required == without_delivery.protective_recovery_required
    assert with_failure.block_new_entries == without_delivery.block_new_entries
    assert with_failure.missing_protection_symbols == without_delivery.missing_protection_symbols
