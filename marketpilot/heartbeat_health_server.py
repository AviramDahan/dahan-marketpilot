"""Read-only HTTP health surface for deployed scheduler heartbeat evidence."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Mapping
from urllib.parse import urlparse

from marketpilot.shared_state import load_dashboard_payload_from_env


DEFAULT_MAX_AGE_SECONDS = 900


def build_heartbeat_health(
    *,
    now: datetime | None = None,
    max_age_seconds: int = DEFAULT_MAX_AGE_SECONDS,
) -> dict[str, object]:
    """Return a sanitized monitor-only heartbeat status from shared state."""

    checked_at = _aware_utc(now or datetime.now(timezone.utc))
    try:
        snapshot = load_dashboard_payload_from_env()
    except Exception:
        return _health_payload(
            status="error",
            checked_at=checked_at,
            latest_heartbeat_at=None,
            age_seconds=None,
            reason="shared_state_read_error",
        )
    if snapshot is None:
        return _health_payload(
            status="missing",
            checked_at=checked_at,
            latest_heartbeat_at=None,
            age_seconds=None,
            reason="heartbeat_missing",
        )

    heartbeat = _mapping(dict(snapshot.payload).get("system_health"))
    if not heartbeat:
        return _health_payload(
            status="missing",
            checked_at=checked_at,
            latest_heartbeat_at=None,
            age_seconds=None,
            reason="heartbeat_missing",
        )

    latest_at = _parse_timestamp(heartbeat.get("timestamp"))
    if latest_at is None:
        return _health_payload(
            status="missing",
            checked_at=checked_at,
            latest_heartbeat_at=None,
            age_seconds=None,
            reason="heartbeat_timestamp_missing",
            worker_state=str(heartbeat.get("status") or "unknown"),
        )

    age_seconds = max(0, int((checked_at - latest_at).total_seconds()))
    status = "ok" if age_seconds <= max_age_seconds else "stale"
    return _health_payload(
        status=status,
        checked_at=checked_at,
        latest_heartbeat_at=latest_at,
        age_seconds=age_seconds,
        reason=None if status == "ok" else "heartbeat_stale",
        worker_state=str(heartbeat.get("status") or "unknown"),
    )


def _health_payload(
    *,
    status: str,
    checked_at: datetime,
    latest_heartbeat_at: datetime | None,
    age_seconds: int | None,
    reason: str | None,
    worker_state: str = "unknown",
) -> dict[str, object]:
    return {
        "status": status,
        "checked_at": checked_at.astimezone(timezone.utc).isoformat(),
        "latest_heartbeat_at": latest_heartbeat_at.astimezone(timezone.utc).isoformat() if latest_heartbeat_at else None,
        "age_seconds": age_seconds,
        "reason": reason,
        "worker_state": worker_state,
        "paper_trading_only": True,
        "monitor_only": True,
        "controls_scheduler": False,
        "controls_orders": False,
        "controls_recovery": False,
    }


def _handler(max_age_seconds: int) -> type[BaseHTTPRequestHandler]:
    class HeartbeatHealthHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - stdlib callback name
            path = urlparse(self.path).path
            if path == "/":
                self._write_json({"status": "service_ok", "paper_trading_only": True}, status_code=200)
                return
            if path != "/heartbeat":
                self._write_json({"status": "not_found", "paper_trading_only": True}, status_code=404)
                return
            payload = build_heartbeat_health(max_age_seconds=max_age_seconds)
            self._write_json(payload, status_code=200)

        def log_message(self, _format: str, *_args: object) -> None:
            return

        def _write_json(self, payload: Mapping[str, object], *, status_code: int) -> None:
            body = json.dumps(dict(payload), sort_keys=True).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return HeartbeatHealthHandler


def serve(*, host: str, port: int, max_age_seconds: int) -> None:
    server = ThreadingHTTPServer((host, port), _handler(max_age_seconds))
    server.serve_forever()


def _parse_timestamp(value: object) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        return _aware_utc(datetime.fromisoformat(str(value).replace("Z", "+00:00")))
    except ValueError:
        return None


def _mapping(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return value
    return {}


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("heartbeat health timestamps must be timezone-aware")
    return value.astimezone(timezone.utc)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Serve read-only MarketPilot heartbeat health JSON.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")))
    parser.add_argument("--max-age-seconds", type=int, default=int(os.environ.get("MARKETPILOT_HEALTH_MAX_AGE_SECONDS", DEFAULT_MAX_AGE_SECONDS)))
    args = parser.parse_args(argv)
    serve(host=args.host, port=args.port, max_age_seconds=args.max_age_seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["build_heartbeat_health", "main", "serve"]
