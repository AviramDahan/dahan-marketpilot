from decimal import Decimal

from marketpilot.risk import RiskRejectionReason, calculate_position_size


def test_position_sizing_uses_risk_amount_divided_by_stop_distance():
    decision = calculate_position_size(
        simulated_equity=100_000,
        available_cash=100_000,
        entry_price=100,
        stop_distance=5,
        reward_risk=2.5,
    )

    assert decision.accepted is True
    assert decision.risk_amount == Decimal("1000.0")
    assert decision.quantity == 150
    assert decision.allocation_amount == Decimal("15000")


def test_invalid_stop_distance_rejects_fail_closed():
    decision = calculate_position_size(
        simulated_equity=100_000,
        available_cash=100_000,
        entry_price=100,
        stop_distance=0,
        reward_risk=2.5,
    )

    assert decision.accepted is False
    assert RiskRejectionReason.INVALID_STOP_DISTANCE in decision.rejection_reasons


def test_reward_risk_below_minimum_rejects():
    decision = calculate_position_size(
        simulated_equity=100_000,
        available_cash=100_000,
        entry_price=100,
        stop_distance=5,
        reward_risk=1.5,
    )

    assert decision.accepted is False
    assert RiskRejectionReason.MINIMUM_REWARD_RISK_NOT_MET in decision.rejection_reasons


def test_cash_shortage_reduces_quantity_when_still_valid():
    decision = calculate_position_size(
        simulated_equity=100_000,
        available_cash=7_500,
        entry_price=100,
        stop_distance=5,
        reward_risk=2.5,
    )

    assert decision.accepted is True
    assert decision.quantity == 75
    assert decision.allocation_amount == Decimal("7500")


def test_cash_shortage_rejects_when_quantity_invalid():
    decision = calculate_position_size(
        simulated_equity=100_000,
        available_cash=50,
        entry_price=100,
        stop_distance=5,
        reward_risk=2.5,
    )

    assert decision.accepted is False
    assert RiskRejectionReason.ZERO_QUANTITY in decision.rejection_reasons
