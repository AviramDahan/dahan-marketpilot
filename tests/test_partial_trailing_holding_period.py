from decimal import Decimal

from marketpilot.exits import build_exit_plan
from marketpilot.setups.base import NumericEvidence


def test_partial_exits_are_modeled_but_not_executed():
    plan = build_exit_plan(
        symbol="MSFT",
        entry_price=100,
        evidence=(NumericEvidence("swing_low", 95, "structural", True),),
    )

    assert plan.partial_exit_rules[0].r_multiple == Decimal("2.0")
    assert plan.partial_exit_rules[0].execute_orders is False


def test_trailing_stop_disabled_and_holding_period_modeled():
    plan = build_exit_plan(
        symbol="MSFT",
        entry_price=100,
        evidence=(NumericEvidence("swing_low", 95, "structural", True),),
    )

    assert plan.trailing_stop.enabled is False
    assert plan.holding_period.maximum_days == 30
