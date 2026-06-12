import pytest

from marketpilot.constants import PAPER_TRADING_ONLY
from marketpilot.safety import SafetyValidationError, validate_safety_config


def test_central_paper_trading_guard_is_true():
    assert PAPER_TRADING_ONLY is True


def test_paper_trading_only_false_fails():
    with pytest.raises(SafetyValidationError, match="paper_trading_only"):
        validate_safety_config({"paper_trading_only": False})


@pytest.mark.parametrize(
    "key",
    [
        "real_broker_enabled",
        "live_money_enabled",
        "leverage_allowed",
        "margin_allowed",
        "short_selling_allowed",
        "options_allowed",
        "futures_allowed",
        "cryptocurrency_allowed",
        "forex_allowed",
        "manual_order_controls_enabled",
    ],
)
def test_unsafe_feature_classes_fail(key):
    with pytest.raises(SafetyValidationError):
        validate_safety_config({"paper_trading_only": True, key: True})


def test_real_broker_credentials_fail_without_leaking_value():
    secret_value = "super-secret-token"
    with pytest.raises(SafetyValidationError) as exc:
        validate_safety_config({"paper_trading_only": True, "broker_api_key": secret_value})

    assert secret_value not in str(exc.value)
    assert "broker_api_key" in str(exc.value)


def test_safe_config_passes():
    validate_safety_config(
        {
            "paper_trading_only": True,
            "dashboard": {"read_only": True, "manual_order_controls_enabled": False},
            "notifications": {"telegram_enabled": False, "delivery_required_for_safety": False},
        }
    )
