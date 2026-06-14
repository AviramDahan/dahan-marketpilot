from dataclasses import FrozenInstanceError

from dashboard.models import DashboardSectionError
from dashboard.redaction import redact_mapping, redact_text


def test_safe_error_status_dictionaries_redact_secret_like_values():
    unsafe = {
        "api_key": "qc-api-key-value",
        "token": "telegram-token-value",
        "password": "plain-password",
        "credential": "credential-value",
        "user_id": "123456",
        "account": "paper-account",
        "chat_id": "-100123",
        "nested": {
            "safe": "visible",
            "secret_name": "DASHBOARD_PASSWORD",
        },
    }

    redacted = redact_mapping(unsafe)

    assert redacted["api_key"] == "[redacted]"
    assert redacted["token"] == "[redacted]"
    assert redacted["password"] == "[redacted]"
    assert redacted["credential"] == "[redacted]"
    assert redacted["user_id"] == "[redacted]"
    assert redacted["account"] == "[redacted]"
    assert redacted["chat_id"] == "[redacted]"
    assert redacted["nested"] == {"safe": "visible", "secret_name": "[redacted]"}


def test_redact_text_masks_known_secret_values_and_secret_markers():
    text = "token=telegram-token-value password=plain-password safe=ok"

    redacted = redact_text(
        text,
        secret_values=("telegram-token-value", "plain-password"),
    )

    assert "telegram-token-value" not in redacted
    assert "plain-password" not in redacted
    assert "token" not in redacted.lower()
    assert "password" not in redacted.lower()
    assert "safe=ok" in redacted


def test_dashboard_section_error_safe_dict_and_immutability():
    error = DashboardSectionError(
        code="quantconnect_error",
        message="Request failed with token=telegram-token-value",
        detail={"api_key": "qc-api-key-value", "safe": "visible"},
        secret_values=("telegram-token-value", "qc-api-key-value"),
    )

    safe = error.to_safe_dict()

    assert safe["code"] == "quantconnect_error"
    assert "telegram-token-value" not in safe["message"]
    assert safe["detail"] == {"api_key": "[redacted]", "safe": "visible"}

    try:
        error.code = "changed"
    except Exception as exc:
        assert isinstance(exc, FrozenInstanceError)
    else:
        raise AssertionError("DashboardSectionError must be immutable.")
