from datetime import datetime, timezone
from decimal import Decimal

from marketpilot.order_lifecycle import (
    OrderIntent,
    OrderLifecycleEvent,
    OrderLifecycleState,
    make_order_idempotency_key,
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
from marketpilot.reconciliation import (
    ReconciliationMismatchType,
    reconcile_quantconnect_state,
)


def _snapshot() -> QuantConnectPaperSnapshot:
    return QuantConnectPaperSnapshot(
        fixture_label="deterministic-test-fixture",
        captured_at=datetime(2026, 6, 14, 14, 0, tzinfo=timezone.utc),
        cash=Decimal("98500"),
        portfolio_equity=Decimal("101250"),
        holdings=(
            QuantConnectHolding(symbol="MSFT", quantity=10, average_price=Decimal("420"), market_price=Decimal("425")),
        ),
        orders=(
            QuantConnectPaperOrder(
                quantconnect_order_id="qc-order-1",
                symbol="MSFT",
                status="filled",
                quantity=10,
                submitted_at=datetime(2026, 6, 14, 14, 1, tzinfo=timezone.utc),
                idempotency_key="intent-msft",
            ),
        ),
        fills=(
            QuantConnectPaperFill(
                quantconnect_order_id="qc-order-1",
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


def test_quantconnect_snapshot_fields_are_authoritative():
    snapshot = _snapshot()

    assert snapshot.authoritative_source == "quantconnect"
    assert snapshot.fixture_label == "deterministic-test-fixture"
    assert snapshot.cash == Decimal("98500")
    assert snapshot.portfolio_equity == Decimal("101250")
    assert snapshot.holdings[0].symbol == "MSFT"
    assert snapshot.orders[0].quantconnect_order_id == "qc-order-1"
    assert snapshot.fills[0].fill_price == Decimal("421.50")
    assert snapshot.deployment_status is QuantConnectDeploymentStatus.RUNNING
    assert snapshot.algorithm_status is QuantConnectAlgorithmStatus.RUNNING
    assert snapshot.performance.total_fills == 1


def test_reconciliation_mismatch_blocks_new_entries_preserves_exits_and_emits_high_severity_event():
    snapshot = _snapshot()
    local_lifecycle = (
        OrderLifecycleEvent(
            idempotency_key="intent-msft",
            previous_state=OrderLifecycleState.SUBMITTED,
            next_state=OrderLifecycleState.SUBMITTED,
            timestamp=datetime(2026, 6, 14, 14, 1, tzinfo=timezone.utc),
            reason="submitted locally before QuantConnect fill",
            payload={"quantconnect_order_id": "local-mirror-stale"},
        ),
    )

    decision = reconcile_quantconnect_state(
        snapshot=snapshot,
        local_lifecycle_events=local_lifecycle,
        local_audit_records=({"event_type": "order_submitted", "correlation_id": "corr-1"},),
        correlation_id="corr-1",
    )

    assert decision.authoritative_source == "quantconnect"
    assert decision.block_new_entries is True
    assert decision.preserve_exits is True
    assert decision.requires_explicit_recovery is True
    assert ReconciliationMismatchType.ORDER_ID in {mismatch.mismatch_type for mismatch in decision.mismatches}
    assert decision.system_event is not None
    assert decision.system_event.event_type == "system"
    assert decision.system_event.severity == "high"
    assert decision.system_event.payload["authoritative_source"] == "quantconnect"


def test_quantconnect_order_ids_and_fills_override_local_mirror_after_submission_but_idempotency_remains_local():
    signal_time = datetime(2026, 6, 14, 13, 30, tzinfo=timezone.utc)
    idempotency_key = make_order_idempotency_key(
        symbol="MSFT",
        strategy_mode="daily_only",
        primary_setup="relative_strength_leader",
        signal_time=signal_time,
        portfolio_epoch="paper-epoch-1",
    )
    intent = OrderIntent(
        idempotency_key=idempotency_key,
        symbol="MSFT",
        primary_setup="relative_strength_leader",
        strategy_mode="daily_only",
        signal_time=signal_time,
        portfolio_epoch="paper-epoch-1",
        quantity=10,
        entry_price=Decimal("420"),
    )
    snapshot = QuantConnectPaperSnapshot(
        fixture_label="deterministic-test-fixture",
        captured_at=datetime(2026, 6, 14, 14, 10, tzinfo=timezone.utc),
        cash=Decimal("95785"),
        portfolio_equity=Decimal("100035"),
        holdings=(
            QuantConnectHolding(symbol="MSFT", quantity=10, average_price=Decimal("421.50"), market_price=Decimal("425")),
        ),
        orders=(
            QuantConnectPaperOrder(
                quantconnect_order_id="qc-authoritative-42",
                symbol="MSFT",
                status="filled",
                quantity=10,
                submitted_at=datetime(2026, 6, 14, 14, 1, tzinfo=timezone.utc),
                idempotency_key=idempotency_key,
            ),
        ),
        fills=(
            QuantConnectPaperFill(
                quantconnect_order_id="qc-authoritative-42",
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

    decision = reconcile_quantconnect_state(
        snapshot=snapshot,
        local_order_intents=(intent,),
        local_lifecycle_events=(),
        local_audit_records=(),
        correlation_id="corr-2",
    )

    assert decision.block_new_entries is False
    assert decision.authoritative_order_ids == {"MSFT": "qc-authoritative-42"}
    assert decision.authoritative_fills["qc-authoritative-42"].fill_price == Decimal("421.50")
    assert decision.local_idempotency_keys == (idempotency_key,)
