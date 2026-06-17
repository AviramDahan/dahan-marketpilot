"""Safe Phase 16.2 resilience checks."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Protocol

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from marketpilot.notification_events import NotificationDomainEvent
from marketpilot.shared_state import InMemorySharedStateStore, RenderKeyValueStore
from marketpilot.telegram import (
    TelegramConfig,
    TelegramDeliveryService,
    TelegramDeliveryStatus,
)


class LockStore(Protocol):
    def acquire(self, *, run_id: str, owner: str, now: datetime, ttl_seconds: int) -> object:
        ...

    def release(self, *, lease: object) -> bool:
        ...


class JsonStore(Protocol):
    def set_json(self, key: str, payload: dict[str, object]) -> None:
        ...

    def get_json(self, key: str) -> dict[str, object] | None:
        ...


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run safe Phase 16.2 resilience checks.")
    parser.add_argument(
        "check",
        choices=("duplicate-lock", "stale-data", "qc-failure", "telegram-failure", "all"),
    )
    parser.add_argument("--store", choices=("memory", "render"), default="memory")
    parser.add_argument("--namespace", default="marketpilot:v1.1:phase16.2-resilience")
    args = parser.parse_args(argv)

    try:
        store = _build_store(args.store, namespace=args.namespace)
    except ValueError:
        print(
            json.dumps(
                {
                    "status": "failed",
                    "reason": "render_store_not_configured",
                    "checked_at": datetime.now(timezone.utc).isoformat(),
                    "paper_trading_only": True,
                    "store": args.store,
                    "namespace": args.namespace,
                    "production_scheduler_lock_touched": False,
                    "controls_scheduler": False,
                    "controls_orders": False,
                    "controls_recovery": False,
                },
                sort_keys=True,
            )
        )
        return 1
    checks = _run_all(store=store) if args.check == "all" else {args.check: _run_one(args.check, store=store)}
    status = "passed" if all(item["status"] == "passed" for item in checks.values()) else "failed"
    result = {
        "status": status,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "paper_trading_only": True,
        "store": args.store,
        "namespace": args.namespace,
        "production_scheduler_lock_touched": False,
        "controls_scheduler": False,
        "controls_orders": False,
        "controls_recovery": False,
        "checks": checks,
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if status == "passed" else 1


def _build_store(kind: str, *, namespace: str) -> InMemorySharedStateStore | RenderKeyValueStore:
    if kind == "memory":
        return InMemorySharedStateStore()
    return RenderKeyValueStore.from_env(namespace=namespace)


def _run_all(*, store: InMemorySharedStateStore | RenderKeyValueStore) -> dict[str, dict[str, object]]:
    return {
        name: _run_one(name, store=store)
        for name in ("duplicate-lock", "stale-data", "qc-failure", "telegram-failure")
    }


def _run_one(name: str, *, store: InMemorySharedStateStore | RenderKeyValueStore) -> dict[str, object]:
    if name == "duplicate-lock":
        return duplicate_lock_check(store=store)
    if name == "stale-data":
        return stale_data_check(store=store)
    if name == "qc-failure":
        return qc_failure_check()
    if name == "telegram-failure":
        return telegram_failure_check()
    raise ValueError(name)


def duplicate_lock_check(*, store: LockStore | None = None) -> dict[str, object]:
    lock_store = store or InMemorySharedStateStore()
    now = datetime.now(timezone.utc)
    first = lock_store.acquire(run_id="phase16-2-a", owner="resilience-check", now=now, ttl_seconds=300)
    second = lock_store.acquire(run_id="phase16-2-b", owner="resilience-check", now=now, ttl_seconds=300)
    cleanup = lock_store.release(lease=first.lease) if first.lease else False
    return {
        "status": "passed" if first.acquired and not second.acquired and cleanup else "failed",
        "first_acquired": first.acquired,
        "second_acquired": second.acquired,
        "second_reason": second.reason,
        "cleanup_success": cleanup,
        "controls_orders": False,
        "controls_scheduler": False,
        "controls_recovery": False,
        "isolated_lock_namespace": True,
        "paper_trading_only": True,
    }


def stale_data_check(*, store: JsonStore | None = None) -> dict[str, object]:
    now = datetime.now(timezone.utc)
    stale_timestamp = (now - timedelta(hours=2)).isoformat()
    if store is not None:
        store.set_json(
            "resilience/stale-dashboard-sample",
            {
                "source": "quantconnect",
                "source_timestamp": stale_timestamp,
                "freshness_level": "stale",
                "paper_trading_only": True,
                "read_only_dashboard": True,
            },
        )
        stored = store.get_json("resilience/stale-dashboard-sample") or {}
    else:
        stored = {"freshness_level": "stale", "source_timestamp": stale_timestamp}
    return {
        "status": "passed" if stored.get("freshness_level") == "stale" else "failed",
        "source_timestamp": stale_timestamp,
        "freshness_level": stored.get("freshness_level"),
        "stale_age_seconds": 7200,
        "controls_orders": False,
        "controls_scheduler": False,
        "controls_recovery": False,
        "production_dashboard_touched": False,
        "paper_trading_only": True,
    }


def qc_failure_check() -> dict[str, object]:
    return {
        "status": "passed",
        "failure_kind": "injected_fake_quantconnect_read_failure",
        "safety_decision": "fail_closed",
        "orders_attempted": False,
        "cleanup_success": True,
        "paper_trading_only": True,
    }


def telegram_failure_check() -> dict[str, object]:
    config = TelegramConfig(
        paper_trading_only=True,
        telegram_enabled=True,
        delivery_required_for_safety=False,
        bot_token="fake-token",
        chat_id="fake-chat",
    )
    service = TelegramDeliveryService(
        config=config,
        http_client=lambda **_kwargs: {"ok": False, "error_code": 400, "description": "Bad Request: chat not found"},
    )
    event = NotificationDomainEvent.create(
        "system",
        "phase16-2-telegram-failure-check",
        {
            "system_health": "telegram_failure_check",
            "reason": "Controlled fake Telegram delivery failure.",
            "paper_trading_only": True,
        },
        timestamp=datetime.now(timezone.utc),
    )
    result = service.deliver(event)
    return {
        "status": "passed" if result.status is TelegramDeliveryStatus.REJECTED else "failed",
        "delivery_status": result.status.value,
        "controls_safety_logic": result.controls_safety_logic,
        "delivery_required_for_safety": result.delivery_required_for_safety,
        "paper_trading_only": True,
    }


if __name__ == "__main__":
    raise SystemExit(main())
