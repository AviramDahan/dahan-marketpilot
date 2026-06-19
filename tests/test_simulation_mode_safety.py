import pytest

from marketpilot.product_modes import assert_simulation_only_safety


def test_simulation_only_accepts_empty_environment():
    capabilities = assert_simulation_only_safety(env={})

    assert capabilities.mode.value == "simulation_only"
    assert capabilities.requires_quantconnect is False


@pytest.mark.parametrize(
    "key",
    [
        "BROKER_API_KEY",
        "BROKER_API_SECRET",
        "LIVE_BROKERAGE_USERNAME",
        "LIVE_BROKERAGE_PASSWORD",
        "REAL_MONEY_ENABLED",
        "ALLOW_REAL_ORDERS",
    ],
)
def test_simulation_only_rejects_live_trading_configuration(key):
    with pytest.raises(RuntimeError, match=key):
        assert_simulation_only_safety(env={key: "present"})


def test_quantconnect_credentials_are_not_required_for_simulation_only():
    capabilities = assert_simulation_only_safety(
        env={
            "QUANTCONNECT_API_TOKEN": "",
            "QUANTCONNECT_USER_ID": "",
            "QC_DEPLOY_ID": "",
        }
    )

    assert capabilities.requires_quantconnect is False
    assert capabilities.submits_quantconnect_orders is False

