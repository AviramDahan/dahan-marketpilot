from datetime import datetime, timezone

from marketpilot.order_lifecycle import make_order_idempotency_key


def test_idempotency_key_is_stable_for_same_logical_signal():
    signal_time = datetime(2026, 6, 14, 20, 0, tzinfo=timezone.utc)

    key_a = make_order_idempotency_key(
        symbol=" msft ",
        strategy_mode="DAILY_ONLY",
        primary_setup="Relative_Strength_Leader",
        signal_time=signal_time,
        portfolio_epoch="Epoch-1",
    )
    key_b = make_order_idempotency_key(
        symbol="MSFT",
        strategy_mode="daily_only",
        primary_setup="relative_strength_leader",
        signal_time=signal_time,
        portfolio_epoch="epoch-1",
    )

    assert key_a == key_b


def test_idempotency_key_changes_when_epoch_or_signal_changes():
    signal_time = datetime(2026, 6, 14, 20, 0, tzinfo=timezone.utc)

    base = make_order_idempotency_key(
        symbol="MSFT",
        strategy_mode="daily_only",
        primary_setup="relative_strength_leader",
        signal_time=signal_time,
        portfolio_epoch="epoch-1",
    )
    other = make_order_idempotency_key(
        symbol="MSFT",
        strategy_mode="daily_only",
        primary_setup="relative_strength_leader",
        signal_time=signal_time,
        portfolio_epoch="epoch-2",
    )

    assert base != other
