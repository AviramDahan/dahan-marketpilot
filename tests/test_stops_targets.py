from decimal import Decimal

import pytest

from marketpilot.exits import build_exit_plan
from marketpilot.setups.base import NumericEvidence


def test_build_exit_plan_uses_swing_low_stop_and_2r_target():
    plan = build_exit_plan(
        symbol="MSFT",
        entry_price=100,
        evidence=(NumericEvidence("swing_low", 95, "structural", True),),
        atr=3,
    )

    assert plan.stop.price == Decimal("95")
    assert plan.stop.source == "swing_low"
    assert plan.target.price == Decimal("110.0")
    assert plan.target.r_multiple == Decimal("2.0")


def test_build_exit_plan_uses_breakout_level_stop():
    plan = build_exit_plan(
        symbol="MSFT",
        entry_price=100,
        evidence=(NumericEvidence("breakout_level", 97, "prior_resistance", True),),
        atr=2,
    )

    assert plan.stop.price == Decimal("97")
    assert plan.target.price == Decimal("106.0")


def test_invalid_stop_rejects_fail_closed():
    with pytest.raises(ValueError, match="below entry"):
        build_exit_plan(
            symbol="MSFT",
            entry_price=100,
            evidence=(NumericEvidence("swing_low", 101, "bad", False),),
        )


def test_atr_sanity_cap_rejects_excessive_stop_distance():
    with pytest.raises(ValueError, match="ATR sanity cap"):
        build_exit_plan(
            symbol="MSFT",
            entry_price=100,
            evidence=(NumericEvidence("swing_low", 80, "too far", False),),
            atr=3,
        )
