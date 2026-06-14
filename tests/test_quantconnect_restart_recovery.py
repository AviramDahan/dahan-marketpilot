from datetime import datetime, timezone
from decimal import Decimal

from marketpilot.quantconnect_paper import (
    QuantConnectAlgorithmStatus,
    QuantConnectDeploymentStatus,
    QuantConnectHolding,
    QuantConnectPaperFill,
    QuantConnectPaperOrder,
    QuantConnectPaperPerformance,
    QuantConnectPaperSnapshot,
    QuantConnectPaperStatusCode,
)
from marketpilot.recovery import QuantConnectRecoveryStatus, recover_from_quantconnect_snapshot


def _snapshot() -> QuantConnectPaperSnapshot:
    return QuantConnectPaperSnapshot(
        fixture_label="deterministic-test-fixture",
        captured_at=datetime(2026, 6, 14, 15, 0, tzinfo=timezone.utc),
        cash=Decimal("95000"),
        portfolio_equity=Decimal("100250"),
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


def test_restart_recovery_rebuilds_active_context_from_quantconnect_first():
    decision = recover_from_quantconnect_snapshot(
        snapshot=_snapshot(),
        local_audit_records=(),
        correlation_id="restart-1",
    )

    assert decision.status is QuantConnectRecoveryStatus.RECOVERED
    assert decision.authoritative_source == "quantconnect"
    assert decision.block_new_entries is False
    assert decision.reconstructed_positions == {"MSFT": 10}
    assert decision.reconstructed_order_ids == ("qc-order-1",)
    assert decision.reconstructed_fill_count == 1


def test_local_audit_history_attaches_after_quantconnect_reconstruction_as_context_only():
    decision = recover_from_quantconnect_snapshot(
        snapshot=_snapshot(),
        local_audit_records=(
            {"event_type": "local_order_intent", "correlation_id": "intent-1", "payload": {"symbol": "MSFT"}},
        ),
        correlation_id="restart-2",
    )

    assert decision.authoritative_source == "quantconnect"
    assert decision.attached_local_audit_count == 1
    assert decision.local_audit_context_only is True
    assert decision.reconstructed_positions == {"MSFT": 10}


def test_quantconnect_unavailable_blocks_new_entries_and_does_not_promote_local_state_to_authority():
    decision = recover_from_quantconnect_snapshot(
        snapshot=None,
        local_audit_records=(
            {"event_type": "local_order_intent", "correlation_id": "intent-1", "payload": {"symbol": "MSFT"}},
        ),
        correlation_id="restart-3",
        unavailable_status=QuantConnectPaperStatusCode.NOT_CONFIGURED,
    )

    assert decision.status is QuantConnectRecoveryStatus.NOT_CONFIGURED
    assert decision.authoritative_source == "quantconnect_unavailable"
    assert decision.block_new_entries is True
    assert decision.requires_explicit_recovery is True
    assert decision.local_audit_context_only is True
    assert decision.reconstructed_positions == {}
    assert "quantconnect_snapshot_unavailable" in decision.recovery_required_reasons
