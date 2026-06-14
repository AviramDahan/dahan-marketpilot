from marketpilot.exits import build_exit_plan, exit_obligations_after_regime_change
from marketpilot.setups.base import NumericEvidence


def test_risk_off_does_not_remove_existing_exit_obligations():
    plan = build_exit_plan(
        symbol="MSFT",
        entry_price=100,
        evidence=(NumericEvidence("swing_low", 95, "structural", True),),
        current_regime="risk_on",
    )

    updated = exit_obligations_after_regime_change(plan, "risk_off")

    assert updated.obligations_active is True
    assert updated.stop == plan.stop
    assert updated.target == plan.target
    assert updated.evidence["exits_remain_authoritative"] is True
