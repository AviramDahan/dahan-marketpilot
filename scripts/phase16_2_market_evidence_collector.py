"""Assemble sanitized Phase 16.2 market-session evidence without fabrication."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.phase16_2_trace_e2e_flow import REQUIRED_SEGMENTS, build_trace, sanitize


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Collect one sanitized Phase 16.2 E2E evidence bundle.")
    parser.add_argument("--correlation-id", required=True)
    parser.add_argument("--signal-json", type=Path)
    parser.add_argument("--scoring-json", type=Path)
    parser.add_argument("--risk-json", type=Path)
    parser.add_argument("--qc-orders-json", type=Path)
    parser.add_argument("--sync-json", type=Path)
    parser.add_argument("--dashboard-json", type=Path)
    parser.add_argument("--telegram-json", type=Path)
    parser.add_argument("--output-json", type=Path)
    args = parser.parse_args(argv)

    payloads = _load_segment_payloads(
        correlation_id=args.correlation_id,
        paths={
            "signal_or_probe": args.signal_json,
            "scoring": args.scoring_json,
            "risk_decision": args.risk_json,
            "qc_order_authority": args.qc_orders_json,
            "sync": args.sync_json,
            "dashboard": args.dashboard_json,
            "telegram": args.telegram_json,
        },
    )
    result = collect_evidence(correlation_id=args.correlation_id, payloads=payloads)
    text = json.dumps(result, sort_keys=True)
    if args.output_json:
        args.output_json.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if result["trace"]["status"] == "passed" else 2


def collect_evidence(*, correlation_id: str, payloads: Mapping[str, Mapping[str, Any]]) -> dict[str, object]:
    sanitized_payloads: list[Mapping[str, Any]] = []
    bundle_segments: dict[str, object] = {}
    for segment in REQUIRED_SEGMENTS:
        payload = payloads.get(segment)
        if payload is None:
            bundle_segments[segment] = {"status": "not_run"}
            continue
        sanitized = sanitize(payload)
        if not isinstance(sanitized, Mapping):
            bundle_segments[segment] = {"status": "invalid_payload"}
            continue
        payload_correlation_id = _extract_payload_correlation_id(sanitized)
        if not payload_correlation_id:
            bundle_segments[segment] = {
                "status": "missing_correlation_id",
                "expected_correlation_id": correlation_id,
            }
            continue
        if payload_correlation_id != correlation_id:
            bundle_segments[segment] = {
                "status": "correlation_mismatch",
                "expected_correlation_id": correlation_id,
                "observed_correlation_id": payload_correlation_id,
            }
            continue
        normalized = dict(sanitized)
        sanitized_payloads.append(normalized)
        bundle_segments[segment] = {"status": "provided", "correlation_id": correlation_id}

    combined_evidence = _combine_trace_payload(correlation_id=correlation_id, payloads=sanitized_payloads)
    trace = build_trace(sanitized_payloads)
    return {
        **combined_evidence,
        "status": trace["status"],
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "paper_trading_only": True,
        "expected_correlation_id": correlation_id,
        "segments": bundle_segments,
        "trace": trace,
        "fabricated_segments": [],
    }


def _load_segment_payloads(*, correlation_id: str, paths: Mapping[str, Path | None]) -> dict[str, Mapping[str, Any]]:
    payloads: dict[str, Mapping[str, Any]] = {}
    for segment, path in paths.items():
        if path is None:
            continue
        loaded = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(loaded, Mapping):
            raise SystemExit(f"{path} must contain a JSON object for {segment}")
        payloads[segment] = dict(loaded)
    return payloads


def _extract_payload_correlation_id(payload: Mapping[str, Any]) -> str | None:
    for key in ("correlation_id", "signal_id", "idempotency_key", "expected_order_tag"):
        value = payload.get(key)
        if value:
            return str(value)
    signal_preview = payload.get("signal_preview")
    if isinstance(signal_preview, Mapping):
        return _extract_payload_correlation_id(signal_preview)
    return None


def _combine_trace_payload(*, correlation_id: str, payloads: list[Mapping[str, Any]]) -> dict[str, object]:
    combined: dict[str, object] = {}
    observed_ids = {_extract_payload_correlation_id(payload) for payload in payloads}
    if observed_ids == {correlation_id}:
        combined["correlation_id"] = correlation_id
    for payload in payloads:
        for key, value in payload.items():
            if key == "correlation_id":
                continue
            combined.setdefault(key, value)
    return combined


if __name__ == "__main__":
    raise SystemExit(main())
