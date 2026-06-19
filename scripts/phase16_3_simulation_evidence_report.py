from __future__ import annotations

"""Phase 16.3 simulation-only MVP evidence gate."""

import argparse
import json
from collections.abc import Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any


SECRET_KEY_FRAGMENTS = ("token", "secret", "password", "credential", "api_key", "apikey", "account_id", "user_id")


def evaluate_simulation_evidence(payload: Mapping[str, Any]) -> dict[str, Any]:
    checks = {
        "product_mode_simulation_only": payload.get("product_mode") == "simulation_only",
        "paper_trading_only": payload.get("paper_trading_only") is True,
        "simulation_only": payload.get("simulation_only") is True,
        "read_only_dashboard": payload.get("read_only_dashboard") is True,
        "dashboard_mutation_disabled": payload.get("dashboard_mutation_allowed") is False,
        "no_real_orders": payload.get("real_orders") is False,
        "quantconnect_not_required": payload.get("quantconnect_required") is False,
        "no_guaranteed_profit_claims": payload.get("guaranteed_profit_claims") is False,
        "no_live_brokerage_path": payload.get("live_brokerage_path") is False,
        "source_timestamp_timezone_aware": _timezone_aware(payload.get("source_timestamp")),
        "portfolio_present": isinstance(payload.get("portfolio"), Mapping),
        "scanner_evidence_present": _count(payload.get("candidates")) + _count(payload.get("rejected_candidates")) > 0,
        "dashboard_evidence_present": _count(payload.get("system")) > 0,
        "telegram_evidence_present": _count(payload.get("notifications")) > 0,
        "no_secret_like_fields": not _contains_secret_like_field(payload),
    }
    passed = all(checks.values())
    return {
        "phase": "16.3",
        "status": "passed" if passed else "blocked_external_not_verified",
        "product_mode": payload.get("product_mode"),
        "paper_trading_only": payload.get("paper_trading_only"),
        "checks": checks,
        "counts": {
            "candidates": _count(payload.get("candidates")),
            "rejected_candidates": _count(payload.get("rejected_candidates")),
            "open_trades": _count(payload.get("open_trades")),
            "closed_trades": _count(payload.get("closed_trades")),
            "notifications": _count(payload.get("notifications")),
            "system": _count(payload.get("system")),
        },
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate Phase 16.3 simulation MVP evidence.")
    parser.add_argument("--evidence-json", required=True, help="Path to sanitized simulation evidence JSON.")
    args = parser.parse_args(argv)

    with Path(args.evidence_json).open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, Mapping):
        raise SystemExit("evidence root must be a JSON object")

    report = evaluate_simulation_evidence(payload)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "passed" else 2


def _timezone_aware(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def _count(value: object) -> int:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return len(value)
    return 0


def _contains_secret_like_field(value: object) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if any(fragment in str(key).lower() for fragment in SECRET_KEY_FRAGMENTS):
                return True
            if _contains_secret_like_field(item):
                return True
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_secret_like_field(item) for item in value)
    return False


if __name__ == "__main__":
    raise SystemExit(main())
