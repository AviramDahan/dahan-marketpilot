from marketpilot.recovery import CorporateActionType, corporate_action_placeholder


def test_split_placeholder_is_safe_recovery_state():
    placeholder = corporate_action_placeholder("msft", CorporateActionType.SPLIT)

    assert placeholder.symbol == "MSFT"
    assert placeholder.action_type is CorporateActionType.SPLIT
    assert placeholder.safe_state == "recovery_required"
    assert placeholder.full_execution_deferred is True


def test_delisting_placeholder_is_safe_recovery_state():
    placeholder = corporate_action_placeholder("MSFT", "delisting")

    assert placeholder.action_type is CorporateActionType.DELISTING
    assert placeholder.full_execution_deferred is True
