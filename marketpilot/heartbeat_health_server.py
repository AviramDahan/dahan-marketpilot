from __future__ import annotations

"""Read-only HTTP health surface for deployed scheduler heartbeat evidence."""


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


def build_dashboard_state_health(
    *,
    now: datetime | None = None,
    max_age_seconds: int = DEFAULT_MAX_AGE_SECONDS,
) -> dict[str, object]:
    """Return a sanitized monitor-only dashboard shared-state summary."""

    checked_at = _aware_utc(now or datetime.now(timezone.utc))
    try:
        snapshot = load_dashboard_payload_from_env()
    except Exception:
        return _dashboard_state_payload(
            status="error",
            checked_at=checked_at,
            source_timestamp=None,
            age_seconds=None,
            reason="shared_state_read_error",
        )
    if snapshot is None:
        return _dashboard_state_payload(
            status="missing",
            checked_at=checked_at,
            source_timestamp=None,
            age_seconds=None,
            reason="dashboard_state_missing",
        )

    payload = dict(snapshot.payload)
    source_timestamp = _parse_timestamp(payload.get("source_timestamp"))
    if source_timestamp is None:
        return _dashboard_state_payload(
            status="missing",
            checked_at=checked_at,
            source_timestamp=None,
            age_seconds=None,
            reason="source_timestamp_missing",
            source=payload.get("source"),
            authority=payload.get("authority"),
            freshness_level=payload.get("freshness_level"),
            read_only_dashboard=payload.get("read_only_dashboard") is not False,
            paper_trading_only=payload.get("paper_trading_only") is not False,
            sync_status=payload.get("sync_status"),
            reconciliation_clean=payload.get("reconciliation_clean"),
            generation=payload.get("generation"),
        )

    age_seconds = max(0, int((checked_at - source_timestamp).total_seconds()))
    status = "ok" if age_seconds <= max_age_seconds else "stale"
    return _dashboard_state_payload(
        status=status,
        checked_at=checked_at,
        source_timestamp=source_timestamp,
        age_seconds=age_seconds,
        reason=None if status == "ok" else "dashboard_state_stale",
        source=payload.get("source"),
        authority=payload.get("authority"),
        freshness_level=payload.get("freshness_level"),
        read_only_dashboard=payload.get("read_only_dashboard") is not False,
        paper_trading_only=payload.get("paper_trading_only") is not False,
        sync_status=payload.get("sync_status"),
        reconciliation_clean=payload.get("reconciliation_clean"),
        generation=payload.get("generation"),
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


def _dashboard_state_payload(
    *,
    status: str,
    checked_at: datetime,
    source_timestamp: datetime | None,
    age_seconds: int | None,
    reason: str | None,
    source: object = None,
    authority: object = None,
    freshness_level: object = None,
    read_only_dashboard: bool = True,
    paper_trading_only: bool = True,
    sync_status: object = None,
    reconciliation_clean: object = None,
    generation: object = None,
) -> dict[str, object]:
    return {
        "status": status,
        "checked_at": checked_at.astimezone(timezone.utc).isoformat(),
        "source": str(source) if source not in (None, "") else None,
        "authority": str(authority) if authority not in (None, "") else None,
        "source_timestamp": source_timestamp.astimezone(timezone.utc).isoformat() if source_timestamp else None,
        "age_seconds": age_seconds,
        "freshness_level": str(freshness_level) if freshness_level not in (None, "") else None,
        "sync_status": str(sync_status) if sync_status not in (None, "") else None,
        "reconciliation_clean": reconciliation_clean is True,
        "generation": _safe_int(generation),
        "reason": reason,
        "read_only_dashboard": read_only_dashboard,
        "paper_trading_only": paper_trading_only,
        "monitor_only": True,
        "controls_scheduler": False,
        "controls_orders": False,
        "controls_recovery": False,
    }


def _safe_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def _handler(max_age_seconds: int) -> type[BaseHTTPRequestHandler]:
    class HeartbeatHealthHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - stdlib callback name
            path = urlparse(self.path).path
            if path == "/":
                self._write_json({"status": "service_ok", "paper_trading_only": True}, status_code=200)
                return
            if path == "/heartbeat":
                payload = build_heartbeat_health(max_age_seconds=max_age_seconds)
                self._write_json(payload, status_code=200)
                return
            if path == "/dashboard-state":
                payload = build_dashboard_state_health(max_age_seconds=max_age_seconds)
                self._write_json(payload, status_code=200)
                return
            else:
                self._write_json({"status": "not_found", "paper_trading_only": True}, status_code=404)
                return

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


__all__ = ["build_dashboard_state_health", "build_heartbeat_health", "main", "serve"]
