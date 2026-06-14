from pathlib import Path

import pytest

from marketpilot.telegram import load_telegram_config


def test_default_telegram_config_is_disabled_and_uses_secret_references_only():
    config = load_telegram_config(env={})

    assert config.paper_trading_only is True
    assert config.telegram_enabled is False
    assert config.delivery_required_for_safety is False
    assert config.token_env_var == "TELEGRAM_BOT_TOKEN"
    assert config.chat_id_env_var == "TELEGRAM_CHAT_ID"
    assert config.bot_token is None
    assert config.chat_id is None
    assert config.can_deliver is False


def test_enabled_telegram_config_requires_external_token_and_chat_id(tmp_path):
    config_path = tmp_path / "notifications.yaml"
    config_path.write_text(
        """
notifications:
  paper_trading_only: true
  telegram_enabled: true
  delivery_required_for_safety: false
  token_env_var: MP_TELEGRAM_BOT_TOKEN
  chat_id_env_var: MP_TELEGRAM_CHAT_ID
""".strip(),
        encoding="utf-8",
    )

    missing = load_telegram_config(config_path, env={})
    assert missing.telegram_enabled is True
    assert missing.can_deliver is False
    assert missing.missing_secret_names == ("MP_TELEGRAM_BOT_TOKEN", "MP_TELEGRAM_CHAT_ID")

    configured = load_telegram_config(
        config_path,
        env={
            "MP_TELEGRAM_BOT_TOKEN": "fake-token-from-external-store",
            "MP_TELEGRAM_CHAT_ID": "fake-chat-from-external-store",
        },
    )
    assert configured.can_deliver is True
    assert configured.bot_token == "fake-token-from-external-store"
    assert configured.chat_id == "fake-chat-from-external-store"


def test_loaded_telegram_config_redacts_external_secret_values(tmp_path):
    config_path = tmp_path / "notifications.yaml"
    config_path.write_text(
        """
notifications:
  paper_trading_only: true
  telegram_enabled: true
  delivery_required_for_safety: false
  token_env_var: MP_TELEGRAM_BOT_TOKEN
  chat_id_env_var: MP_TELEGRAM_CHAT_ID
""".strip(),
        encoding="utf-8",
    )
    token_value = "fake-token-from-external-store"
    chat_value = "fake-chat-from-external-store"

    config = load_telegram_config(
        config_path,
        env={
            "MP_TELEGRAM_BOT_TOKEN": token_value,
            "MP_TELEGRAM_CHAT_ID": chat_value,
        },
    )

    safe = config.to_safe_dict()
    assert safe["bot_token"] == "[redacted]"
    assert safe["chat_id"] == "[redacted]"
    assert token_value not in repr(config)
    assert chat_value not in repr(config)
    assert token_value not in str(safe)
    assert chat_value not in str(safe)


def test_repository_config_rejects_committed_secret_values(tmp_path):
    config_path = tmp_path / "notifications.yaml"
    config_path.write_text(
        """
notifications:
  paper_trading_only: true
  telegram_enabled: true
  delivery_required_for_safety: false
  token_env_var: MP_TELEGRAM_BOT_TOKEN
  chat_id_env_var: MP_TELEGRAM_CHAT_ID
  bot_token: not-a-real-committed-token
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="external secret store"):
        load_telegram_config(config_path, env={})


def test_committed_notifications_config_contains_no_secret_values():
    text = Path("config/notifications.yaml").read_text(encoding="utf-8")

    assert "paper_trading_only: true" in text
    assert "delivery_required_for_safety: false" in text
    assert "bot_token:" not in text
    assert "chat_id:" not in text
    assert "TELEGRAM_BOT_TOKEN" in text
    assert "TELEGRAM_CHAT_ID" in text
