"""Verify deployed Phase 16.1 go-live evidence without mutating trading state."""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Mapping

from marketpilot.shared_state import load_dashboard_payload_from_env


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only Render go-live verification.")
    parser.add_argument("--dashboard-url", default=os.environ.get("DASHBOARD_HEALTH_URL"))
    parser.add_argument("--require-dashboard-url", action="store_true")
    parser.add_argument("--require-shared-state", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=10)
    args = parser.parse_args(argv)

    checks = {
        "dashboard_url": _check_dashboard_url(args.dashboard_url, timeout_seconds=args.timeout_seconds),
        "shared_state": _check_shared_state(),
        "local_computer_independence": {
            "status": "operator_evidence_required",
            "detail": "Confirm Render web and worker evidence while local computer is off or disconnected.",
        },
    }
    status = _overall_status(
        checks,
        require_dashboard_url=args.require_dashboard_url,
        require_shared_state=args.require_shared_state,
    )
    result = {
        "status": status,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "paper_trading_only": True,
        "checks": checks,
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if status == "passed" else 2


def _check_dashboard_url(url: str | None, *, timeout_seconds: int) -> dict[str, object]:
    if not url:
        return {"status": "not_run", "reason": "DASHBOARD_HEALTH_URL_missing"}
    safe_url = _redact_url(url)
    try:
        request = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            return {
                "status": "passed" if 200 <= int(response.status) < 500 else "failed",
                "http_status": int(response.status),
                "url": safe_url,
            }
    except urllib.error.HTTPError as exc:
        return {"status": "passed" if 200 <= exc.code < 500 else "failed", "http_status": exc.code, "url": safe_url}
    except Exception as exc:
        return {"status": "failed", "reason": type(exc).__name__, "url": safe_url}


def _check_shared_state() -> dict[str, object]:
    try:
        snapshot = load_dashboard_payload_from_env()
    except Exception as exc:
        return {"status": "failed", "reason": type(exc).__name__, "detail": _redact_text(str(exc))}
    if snapshot is None:
        return {"status": "not_run", "reason": "REDIS_URL_missing_or_dashboard_payload_absent"}
    payload = dict(snapshot.payload)
    return {
        "status": "passed",
        "key": snapshot.key,
        "source": payload.get("source"),
        "authority": payload.get("authority"),
        "fixture_label": payload.get("fixture_label"),
        "source_timestamp": payload.get("source_timestamp"),
        "paper_trading_only": payload.get("paper_trading_only") is True,
    }


def _overall_status(
    checks: Mapping[str, Mapping[str, object]],
    *,
    require_dashboard_url: bool,
    require_shared_state: bool,
) -> str:
    if any(check.get("status") == "failed" for check in checks.values()):
        return "failed"
    required = []
    if require_dashboard_url:
        required.append(checks["dashboard_url"])
    if require_shared_state:
        required.append(checks["shared_state"])
    if required and all(check.get("status") == "passed" for check in required):
        return "passed"
    return "blocked_external_not_verified"


def _redact_url(url: str) -> str:
    if "?" not in url:
        return url
    return url.split("?", 1)[0] + "?[redacted]"


def _redact_text(value: str) -> str:
    redacted = value
    for key in ("REDIS_URL", "DASHBOARD_PASSWORD", "TOKEN", "SECRET", "PASSWORD"):
        redacted = redacted.replace(key.lower(), "[redacted]").replace(key, "[redacted]")
    return redacted


if __name__ == "__main__":
    raise SystemExit(main())
