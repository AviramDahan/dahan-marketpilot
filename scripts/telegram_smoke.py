"""Send a safe Telegram smoke-test alert using local environment secrets.

This script is operator-run only. It loads `.env.local` if present, reads the
configured Telegram env vars, and sends a paper-only test message through the
same delivery boundary used by the application.
"""

from __future__ import annotations

import os
from pathlib import Path

from marketpilot.notification_events import NotificationDomainEvent
from marketpilot.telegram import TelegramConfig, TelegramDeliveryService, load_telegram_config


ROOT = Path(__file__).resolve().parents[1]


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def main() -> int:
    _load_env_file(ROOT / ".env.local")
    config = load_telegram_config(
        ROOT / "config" / "notifications.yaml",
        env=os.environ,
    )
    if os.environ.get("MARKETPILOT_TELEGRAM_SMOKE_ENABLED") == "1":
        config = TelegramConfig(
            paper_trading_only=config.paper_trading_only,
            telegram_enabled=True,
            delivery_required_for_safety=config.delivery_required_for_safety,
            token_env_var=config.token_env_var,
            chat_id_env_var=config.chat_id_env_var,
            bot_token=config.bot_token,
            chat_id=config.chat_id,
            message_max_chars=config.message_max_chars,
        )

    if not config.telegram_enabled:
        print("Telegram delivery is disabled in config/notifications.yaml.")
        print("Set MARKETPILOT_TELEGRAM_SMOKE_ENABLED=1 only for this smoke test environment.")
        return 2

    if config.missing_secret_names:
        print("Missing required Telegram secret environment variables:")
        for name in config.missing_secret_names:
            print(f"- {name}")
        return 2

    event = NotificationDomainEvent.create(
        event_type="system",
        severity="info",
        correlation_id="operator-telegram-smoke-test",
        payload={
            "system_health": "telegram_smoke_test",
            "reason": "Operator verified safe Paper Trading notification delivery.",
        },
    )
    result = TelegramDeliveryService(config=config).deliver(event)
    print(result.to_safe_dict())
    return 0 if result.delivered else 1


if __name__ == "__main__":
    raise SystemExit(main())
