from marketpilot.recovery import RecoveryMismatch, reconcile_restart_state


def test_quantconnect_wins_on_restart_mismatch():
    decision = reconcile_restart_state(
        local_state={
            "order_state": "submitted",
            "fills": 0,
            "holdings": {"MSFT": 0},
            "cash": 1000,
            "open_positions": 0,
        },
        quantconnect_snapshot={
            "order_state": "filled",
            "fills": 1,
            "holdings": {"MSFT": 10},
            "cash": 0,
            "open_positions": 1,
        },
    )

    assert decision.quantconnect_wins is True
    assert decision.local_state_marked_mismatched is True
    assert set(decision.mismatches) == {
        RecoveryMismatch.ORDER_STATE,
        RecoveryMismatch.FILLS,
        RecoveryMismatch.HOLDINGS,
        RecoveryMismatch.CASH,
        RecoveryMismatch.OPEN_POSITIONS,
    }
    assert decision.event_type == "recovery_mismatch"
