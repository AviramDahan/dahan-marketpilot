from datetime import datetime, timezone
from decimal import Decimal

from marketpilot.order_lifecycle import OrderIntent, OrderLifecycleState, make_order_idempotency_key


def test_order_lifecycle_states_cover_phase_6_contract():
    assert {state.value for state in OrderLifecycleState} == {
        "planned",
        "submitted",
        "partially_filled",
        "filled",
        "rejected",
        "canceled",
        "protective_orders_pending",
        "open",
        "partially_closed",
        "closed",
    }


def test_order_intent_is_audit_intent_shape_not_submission_object():
    signal_time = datetime(2026, 6, 14, tzinfo=timezone.utc)
    intent = OrderIntent(
        idempotency_key=make_order_idempotency_key(
            symbol="MSFT",
            strategy_mode="daily_only",
            primary_setup="relative_strength_leader",
            signal_time=signal_time,
            portfolio_epoch="epoch-1",
        ),
        symbol="MSFT",
        primary_setup="relative_strength_leader",
        strategy_mode="daily_only",
        signal_time=signal_time,
        portfolio_epoch="epoch-1",
        quantity=10,
        entry_price=Decimal("100"),
    )

    assert intent.idempotency_key.startswith("order-intent-")
    assert not hasattr(intent, "submit")
    assert not hasattr(intent, "cancel")
