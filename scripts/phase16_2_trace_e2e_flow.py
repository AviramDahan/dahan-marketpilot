"""Build a sanitized Phase 16.2 E2E Paper flow trace from evidence JSON."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


REQUIRED_SEGMENTS = (
    "signal_or_probe",
    "scoring",
    "risk_decision",
    "qc_order_authority",
    "sync",
    "dashboard",
    "telegram",
)
SECRET_KEY_HINTS = ("token", "secret", "password", "credential", "api_key", "chat_id")
SECRET_VALUE_PATTERNS = (
    re.compile(r"\b\d{8,12}:[A-Za-z0-9_-]{25,}\b"),
    re.compile(r"\b[a-f0-9]{48,}\b", re.IGNORECASE),
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize Phase 16.2 E2E flow evidence.")
    parser.add_argument("--evidence-json", type=Path, action="append", default=[])
    args = parser.parse_args(argv)

    payloads = [_load_json(path) for path in args.evidence_json]
    result = build_trace(payloads)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "passed" else 2


def build_trace(payloads: list[Mapping[str, Any]]) -> dict[str, object]:
    segments: dict[str, dict[str, object]] = {name: {"status": "not_run"} for name in REQUIRED_SEGMENTS}
    correlation_ids: set[str] = set()
    segment_correlation_ids: set[str] = set()
    for payload in payloads:
        sanitized = sanitize(payload)
        correlation_id = _extract_correlation_id(sanitized)
        if correlation_id:
            correlation_ids.add(correlation_id)
        for segment in REQUIRED_SEGMENTS:
            if _payload_proves_segment(segment, sanitized):
                segments[segment] = {
                    "status": "passed",
                    "correlation_id": correlation_id,
                    "evidence": _summarize_payload(segment, sanitized),
                }
                if correlation_id:
                    segment_correlation_ids.add(correlation_id)
    missing = [name for name, segment in segments.items() if segment["status"] != "passed"]
    correlation_mismatch = len(segment_correlation_ids) > 1
    status = "passed" if not missing and len(segment_correlation_ids) == 1 else "blocked_external_not_verified"
    return {
        "status": status,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "paper_trading_only": True,
        "correlation_ids": sorted(correlation_ids),
        "segment_correlation_ids": sorted(segment_correlation_ids),
        "correlation_mismatch": correlation_mismatch,
        "missing_segments": missing,
        "segments": segments,
    }


def sanitize(value: Any) -> Any:
    if isinstance(value, Mapping):
        clean: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            if any(hint in key_text.lower() for hint in SECRET_KEY_HINTS):
                clean[key_text] = "[redacted]"
            else:
                clean[key_text] = sanitize(item)
        return clean
    if isinstance(value, list):
        return [sanitize(item) for item in value[:50]]
    if isinstance(value, str):
        redacted = value
        for pattern in SECRET_VALUE_PATTERNS:
            redacted = pattern.sub("[redacted]", redacted)
        return redacted[:500]
    return value


def _load_json(path: Path) -> Mapping[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, Mapping):
        raise SystemExit(f"{path} must contain a JSON object")
    return loaded


def _extract_correlation_id(payload: Mapping[str, Any]) -> str | None:
    for key in ("correlation_id", "signal_id", "idempotency_key", "expected_order_tag"):
        value = payload.get(key)
        if value:
            return str(value)
    signal_preview = payload.get("signal_preview")
    if isinstance(signal_preview, Mapping):
        return _extract_correlation_id(signal_preview)
    return None


def _payload_proves_segment(segment: str, payload: Mapping[str, Any]) -> bool:
    status = str(payload.get("status") or "").lower()
    if segment == "signal_or_probe":
        return bool(payload.get("signal_preview") or payload.get("signal") or "probe" in status)
    if segment == "scoring":
        return bool(payload.get("score") or payload.get("ranking") or payload.get("production_result"))
    if segment == "risk_decision":
        risk = payload.get("risk_decision")
        if isinstance(risk, Mapping):
            return risk.get("accepted") in {True, False} or bool(risk.get("status"))
        if isinstance(risk, str):
            return risk.strip().lower() in {"accepted", "rejected", "blocked", "passed"}
        return bool(payload.get("order_intent"))
    if segment == "qc_order_authority":
        if payload.get("orders_authority_status") in {"submitted", "filled", "rejected", "passed"}:
            return True
        order_status = str(payload.get("order_status") or payload.get("status") or "").lower()
        return order_status in {"submitted", "filled", "rejected", "passed"}
    if segment == "sync":
        return bool(payload.get("source") == "quantconnect" and payload.get("source_timestamp"))
    if segment == "dashboard":
        return bool(payload.get("dashboard") or payload.get("dashboard_url") or payload.get("freshness_level"))
    if segment == "telegram":
        return status == "delivered" or payload.get("telegram_message_id") is not None
    return False


def _summarize_payload(segment: str, payload: Mapping[str, Any]) -> dict[str, object]:
    summary_keys = (
        "status",
        "correlation_id",
        "signal_id",
        "expected_order_tag",
        "order_status",
        "orders_authority_status",
        "source",
        "source_timestamp",
        "freshness_level",
        "telegram_message_id",
        "paper_trading_only",
    )
    summary = {key: payload[key] for key in summary_keys if key in payload}
    summary["segment"] = segment
    return summary


if __name__ == "__main__":
    raise SystemExit(main())
