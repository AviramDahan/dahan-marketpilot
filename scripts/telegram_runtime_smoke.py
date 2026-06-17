"""Send a safe Telegram event through the production runtime dependency path."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from marketpilot.notification_events import NotificationDomainEvent
from marketpilot.production_runner import build_production_dependencies_from_env


ROOT = Path(__file__).resolve().parents[1]


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() and key.strip() not in os.environ:
            os.environ[key.strip()] = value.strip().strip('"').strip("'")


def main() -> int:
    _load_env_file(ROOT / ".env.local")
    if os.environ.get("MARKETPILOT_RUNTIME_TELEGRAM_SMOKE_ENABLED") != "1":
        print(
            json.dumps(
                {
                    "status": "not_run",
                    "reason": "MARKETPILOT_RUNTIME_TELEGRAM_SMOKE_ENABLED_not_set",
                    "paper_trading_only": True,
                },
                sort_keys=True,
            )
        )
        return 2

    deps = build_production_dependencies_from_env(env=os.environ)
    if deps.notification_sink is None:
        print(
            json.dumps(
                {
                    "status": "blocked_external_not_verified",
                    "reason": "telegram_runtime_sink_not_configured",
                    "paper_trading_only": True,
                },
                sort_keys=True,
            )
        )
        return 2

    event = NotificationDomainEvent.create(
        event_type="system",
        severity="info",
        correlation_id="runtime-telegram-smoke-test",
        payload={
            "system_health": "runtime_telegram_smoke_test",
            "reason": "Operator verified production runtime notification sink.",
            "paper_trading_only": True,
        },
        timestamp=datetime.now(timezone.utc),
    )
    delivered = deps.notification_sink.emit(event)
    print(
        json.dumps(
            {
                "status": "delivered" if delivered else "failed",
                "event_type": event.event_type,
                "correlation_id": event.correlation_id,
                "paper_trading_only": True,
            },
            sort_keys=True,
        )
    )
    return 0 if delivered else 1


if __name__ == "__main__":
    raise SystemExit(main())
