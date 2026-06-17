"""Run a guarded QuantConnect Object Store paper signal smoke.

SIMULATED PAPER TRADING ONLY - NOT FINANCIAL ADVICE.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from marketpilot.qc_api import QCApiClient


ENABLE_ENV = "MARKETPILOT_QC_OBJECT_STORE_SMOKE_ENABLED"
REQUIRED_ENV = (
    "QUANTCONNECT_USER_ID",
    "QUANTCONNECT_API_TOKEN",
    "QC_PROJECT_ID",
)
DEPLOY_ENV = ("QC_NODE_ID", "QC_VERSION_ID")
SAFE_ID_ENV = (
    "QC_PROJECT_ID",
    "QC_ORGANIZATION_ID",
    "QC_DEPLOY_ID",
    "QC_COMPILE_ID",
    "QC_NODE_ID",
    "QC_VERSION_ID",
)
SECRET_MARKERS = ("TOKEN", "SECRET", "PASSWORD", "AUTH")
RECEIPT_MARKERS = (
    "MarketPilot Object Store signal received.",
    "MarketPilot object_store accepted:",
    "MarketPilot command rejected:",
)


def build_object_store_signal(*, now_utc: datetime | None = None) -> dict[str, object]:
    now = now_utc or datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%d%H%M%S")
    return {
        "command_type": "marketpilot_signal",
        "correlation_id": f"qc-object-store-smoke-{stamp}",
        "signal_id": f"qc-object-store-sig-{stamp}",
        "idempotency_key": f"qc-object-store-order-{stamp}",
        "symbol": "SPY",
        "quantity": 1,
        "signal_time_utc": now.isoformat(),
        "expires_at_utc": (now + timedelta(minutes=20)).isoformat(),
        "strategy_mode": "daily_only",
        "primary_setup": "object_store_smoke_test",
        "paper_trading_only": True,
        "command_delivery_is_order_execution": False,
    }


def build_object_store_key(*, project_id: int, now_utc: datetime | None = None) -> str:
    now = now_utc or datetime.now(timezone.utc)
    return f"{project_id}/marketpilot/signals/object-store-smoke-{now.strftime('%Y%m%d%H%M%S')}.json"


def summarize_env() -> dict[str, str]:
    summary: dict[str, str] = {}
    for name in REQUIRED_ENV + SAFE_ID_ENV:
        if name in summary:
            continue
        value = os.environ.get(name, "").strip()
        if not value:
            summary[name] = "missing"
        elif any(marker in name.upper() for marker in SECRET_MARKERS):
            summary[name] = "configured_redacted"
        else:
            summary[name] = value
    return summary


def sanitize(value: Any) -> Any:
    if isinstance(value, Mapping):
        clean: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            if any(marker in key_text.upper() for marker in SECRET_MARKERS):
                clean[key_text] = "REDACTED"
            else:
                clean[key_text] = sanitize(item)
        return clean
    if isinstance(value, list):
        return [sanitize(item) for item in value[:20]]
    if isinstance(value, str) and len(value) > 240:
        return f"{value[:240]}..."
    return value


def run_smoke(
    *,
    command_label: str,
    dry_run: bool,
    diagnose_only: bool,
    deploy: bool,
    cleanup: bool,
    file_name: str,
    restore_original: bool,
    compile_polls: int,
    compile_poll_seconds: int,
    polls: int,
    poll_seconds: int,
    stop_after_deploy: bool = True,
) -> dict[str, object]:
    _require_enabled()
    now = datetime.now(timezone.utc)
    project_id = _read_int_env("QC_PROJECT_ID", default=32900381 if dry_run else None)
    key = build_object_store_key(project_id=project_id, now_utc=now)
    signal = build_object_store_signal(now_utc=now)
    expected_order_tag = f"mp:{signal['signal_id']}:{signal['idempotency_key']}"
    result: dict[str, object] = {
        "status": "dry_run" if dry_run else "running",
        "checked_at_utc": now.isoformat(),
        "paper_trading_only": True,
        "command_label": command_label,
        "object_store_key": key,
        "file_name": file_name,
        "restore_original": restore_original,
        "deploy": deploy,
        "diagnose_only": diagnose_only,
        "cleanup": cleanup,
        "stop_after_deploy": stop_after_deploy,
        "environment": summarize_env(),
        "signal_preview": sanitize(signal),
        "expected_order_tag": expected_order_tag,
    }
    if dry_run:
        return result

    client = QCApiClient()
    organization_id = os.environ.get("QC_ORGANIZATION_ID", "").strip() or client.discover_organization_id()
    result["organization_id"] = organization_id

    content = json.dumps(signal, sort_keys=True).encode("utf-8")
    preflight = _run_object_store_preflight(
        client=client,
        organization_id=organization_id,
        project_id=project_id,
        key=key,
        content=content,
        cleanup_after_success=cleanup and diagnose_only,
    )
    result["object_store_preflight"] = sanitize(preflight)
    result["object_store_status"] = preflight["status"]
    result["object_set"] = sanitize(preflight.get("object_set", {}))
    if "object_properties" in preflight:
        result["object_properties"] = sanitize(preflight["object_properties"])
    if "cleanup_success" in preflight:
        result["cleanup_success"] = preflight["cleanup_success"]
    if diagnose_only:
        result["status"] = preflight["status"]
        return result
    if not preflight["write_available"]:
        result["status"] = preflight["status"]
        result["deploy_skipped"] = True
        return result

    if deploy:
        for name in DEPLOY_ENV:
            _read_env(name)
        original_read = client.read_project_file(project_id=project_id, name=file_name)
        original_content = _extract_project_file_content(original_read, file_name)
        injected_content = _inject_object_store_key(_local_lean_main_content(), key)
        try:
            result["file_update_success"] = client.update_project_file_content(
                project_id=project_id,
                name=file_name,
                content=injected_content,
            )
            compile_create = client.create_compile(project_id=project_id)
            compile_id = str(compile_create.get("compileId") or compile_create.get("CompileId") or "")
            result["compile_create"] = sanitize(compile_create)
            result["compile_id"] = compile_id
            result["compile_observations"] = _poll_compile(
                client=client,
                project_id=project_id,
                compile_id=compile_id,
                polls=compile_polls,
                poll_seconds=compile_poll_seconds,
            )
            deploy_response = client.create_live_algorithm(
                project_id=project_id,
                compile_id=compile_id or _read_env("QC_COMPILE_ID"),
                node_id=_read_env("QC_NODE_ID"),
                version_id=_read_env("QC_VERSION_ID"),
                data_providers={"QuantConnectBrokerage": {"id": "QuantConnectBrokerage"}},
            )
            result["deploy_response"] = sanitize(_summarize_deploy_response(deploy_response))
            if not deploy_response.get("success"):
                result["status"] = "deploy_failed"
                return result
            deploy_id = _extract_deploy_id(deploy_response) or _read_env("QC_DEPLOY_ID")
        finally:
            if restore_original and original_content:
                result["restore_original_success"] = client.update_project_file_content(
                    project_id=project_id,
                    name=file_name,
                    content=original_content,
                )
    else:
        deploy_id = _read_env("QC_DEPLOY_ID")
    result["deploy_id"] = deploy_id

    observations: list[dict[str, object]] = []
    for index in range(polls):
        if index:
            time.sleep(poll_seconds)
        logs = client.read_live_logs(
            project_id=project_id,
            deploy_id=deploy_id,
            start_line=0,
            end_line=250,
            deployment_logs=True,
        )
        orders = client.read_live_orders_page(
            project_id=project_id,
            deploy_id=deploy_id,
            start=0,
            end=20,
        )
        live_logs = logs.get("LiveLogs") or logs.get("logs") or []
        raw_orders = orders.get("orders") or []
        order_rows = list(raw_orders.values()) if isinstance(raw_orders, dict) else list(raw_orders)
        receipt_observed = any(marker in str(live_logs) for marker in RECEIPT_MARKERS)
        marketpilot_orders = [
            order
            for order in order_rows
            if isinstance(order, Mapping)
            and str(order.get("tag") or order.get("Tag") or "").startswith("mp:")
        ]
        tagged_orders = [
            order
            for order in marketpilot_orders
            if str(order.get("tag") or order.get("Tag") or "") == expected_order_tag
        ]
        observations.append(
            {
                "poll": index,
                "live_log_count": len(live_logs) if isinstance(live_logs, list) else 0,
                "receipt_observed": receipt_observed,
                "live_logs_tail": sanitize(live_logs[-10:] if isinstance(live_logs, list) else live_logs),
                "order_count": len(order_rows),
                "marketpilot_order_count": len(marketpilot_orders),
                "tagged_order_count": len(tagged_orders),
                "tagged_orders": sanitize(tagged_orders[:5]),
            }
        )
        if tagged_orders:
            break

    result["observations"] = observations
    result["status"] = _status_from_observations(observations)

    if cleanup:
        result["cleanup_success"] = client.delete_object_store_file(
            organization_id=organization_id,
            project_id=project_id,
            key=key,
        )
    if deploy and stop_after_deploy:
        result["stop_attempted"] = True
        result["stop_success"] = client.stop_live_algorithm(project_id=project_id)
    elif deploy:
        result["stop_attempted"] = False
    return result


def _run_object_store_preflight(
    *,
    client: QCApiClient,
    organization_id: str,
    project_id: int,
    key: str,
    content: bytes,
    cleanup_after_success: bool,
) -> dict[str, object]:
    upload = client.upload_object_store_file(
        organization_id=organization_id,
        project_id=project_id,
        key=key,
        content=content,
    )
    status = _classify_object_store_set(upload)
    preflight: dict[str, object] = {
        "status": status,
        "write_available": status == "object_store_write_available",
        "object_set": sanitize(upload),
    }
    if preflight["write_available"]:
        preflight["object_properties"] = sanitize(
            client.read_object_store_metadata(organization_id=organization_id, key=key)
        )
        if cleanup_after_success:
            preflight["cleanup_success"] = client.delete_object_store_file(
                organization_id=organization_id,
                project_id=project_id,
                key=key,
            )
    else:
        try:
            preflight["object_properties"] = sanitize(
                client.read_object_store_metadata(organization_id=organization_id, key=key)
            )
        except Exception as exc:  # pragma: no cover - defensive external diagnostic
            preflight["object_properties_error"] = {
                "type": type(exc).__name__,
                "detail": str(exc)[:240],
            }
    return preflight


def _classify_object_store_set(response: Mapping[str, object]) -> str:
    if response.get("success") is True:
        return "object_store_write_available"
    errors = " ".join(str(item) for item in response.get("errors", [])).lower()
    if "organization not found" in errors or "permission" in errors or "paid" in errors:
        return "blocked_external_object_store_permission_or_paid_tier_required"
    return "blocked_external_object_store_write_not_verified"


def _local_lean_main_content() -> str:
    return (ROOT / "lean" / "main.py").read_text(encoding="utf-8")


def _inject_object_store_key(content: str, key: str) -> str:
    marker = '    MARKETPILOT_OBJECT_STORE_SIGNAL_KEY = ""'
    replacement = f'    MARKETPILOT_OBJECT_STORE_SIGNAL_KEY = "{key}"'
    if marker not in content:
        raise SystemExit("Could not find MARKETPILOT_OBJECT_STORE_SIGNAL_KEY marker in lean/main.py")
    return content.replace(marker, replacement, 1)


def _poll_compile(
    *,
    client: QCApiClient,
    project_id: int,
    compile_id: str,
    polls: int,
    poll_seconds: int,
) -> list[dict[str, object]]:
    observations: list[dict[str, object]] = []
    for index in range(max(polls, 1)):
        if index:
            time.sleep(poll_seconds)
        response = client.read_compile(project_id=project_id, compile_id=compile_id)
        state = str(response.get("state") or response.get("State") or "")
        observations.append({"poll": index, "state": state, "response": sanitize(response)})
        if state in {"BuildSuccess", "BuildError"}:
            break
    return observations


def _extract_project_file_content(response: Mapping[str, object], file_name: str) -> str:
    files = response.get("files") or response.get("Files")
    if isinstance(files, list):
        for item in files:
            if isinstance(item, Mapping) and str(item.get("name") or item.get("Name")) == file_name:
                return str(item.get("content") or item.get("Content") or "")
    if isinstance(files, Mapping):
        item = files.get(file_name)
        if isinstance(item, Mapping):
            return str(item.get("content") or item.get("Content") or "")
        if isinstance(item, str):
            return item
    return str(response.get("content") or response.get("Content") or "")


def _summarize_deploy_response(response: Mapping[str, object]) -> dict[str, object]:
    summary = _strip_file_contents(dict(response))
    live = summary.get("live")
    if isinstance(live, Mapping):
        files = live.get("files")
        if isinstance(files, list):
            live["file_count"] = len(files)
            live["files"] = [
                {
                    "name": item.get("name"),
                    "projectId": item.get("projectId"),
                    "modified": item.get("modified"),
                    "content_length": len(str(item.get("content") or item.get("Content") or "")),
                }
                for item in files
                if isinstance(item, Mapping)
            ][:40]
    return summary


def _strip_file_contents(value: object) -> object:
    if isinstance(value, dict):
        clean: dict[str, object] = {}
        for key, item in value.items():
            if str(key) in {"content", "Content"}:
                clean["content_length"] = len(str(item or ""))
            else:
                clean[str(key)] = _strip_file_contents(item)
        return clean
    if isinstance(value, list):
        return [_strip_file_contents(item) for item in value]
    return value


def _extract_deploy_id(response: Mapping[str, object]) -> str:
    for key in ("deployId", "DeployId", "algorithmId", "AlgorithmId", "liveId"):
        value = response.get(key)
        if value:
            return str(value)
    live = response.get("live")
    if isinstance(live, Mapping):
        for key in ("deployId", "DeployId", "algorithmId", "AlgorithmId", "liveId"):
            value = live.get(key)
            if value:
                return str(value)
    return ""


def _status_from_observations(observations: list[dict[str, object]]) -> str:
    if any(obs.get("tagged_order_count") for obs in observations):
        return "object_store_delivery_order_observed"
    if any(obs.get("receipt_observed") for obs in observations):
        return "object_store_delivery_receipt_or_rejection_observed"
    return "object_store_written_no_algorithm_receipt_observed"


def _require_enabled() -> None:
    if os.environ.get(ENABLE_ENV, "").strip() != "1":
        raise SystemExit(f"Set {ENABLE_ENV}=1 to run this paper-only Object Store smoke.")


def _read_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def _read_int_env(name: str, *, default: int | None = None) -> int:
    value = os.environ.get(name, "").strip()
    if not value:
        if default is not None:
            return default
        raise SystemExit(f"Missing required environment variable: {name}")
    return int(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--command-label", default="object_store_signal_probe")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--diagnose-only", action="store_true")
    parser.add_argument("--skip-deploy", action="store_true")
    parser.add_argument("--file-name", default="main.py")
    parser.add_argument("--no-restore-original", action="store_true")
    parser.add_argument("--no-cleanup", action="store_true")
    parser.add_argument(
        "--keep-running",
        action="store_true",
        help="Leave the temporary Paper deployment running for explicit next-open observation.",
    )
    parser.add_argument("--compile-polls", type=int, default=12)
    parser.add_argument("--compile-poll-seconds", type=int, default=5)
    parser.add_argument("--polls", type=int, default=12)
    parser.add_argument("--poll-seconds", type=int, default=5)
    args = parser.parse_args(argv)

    output = run_smoke(
        command_label=args.command_label,
        dry_run=args.dry_run,
        diagnose_only=args.diagnose_only,
        deploy=not args.skip_deploy,
        cleanup=not args.no_cleanup,
        file_name=args.file_name,
        restore_original=not args.no_restore_original,
        compile_polls=args.compile_polls,
        compile_poll_seconds=args.compile_poll_seconds,
        polls=args.polls,
        poll_seconds=args.poll_seconds,
        stop_after_deploy=not args.keep_running,
    )
    print(json.dumps(sanitize(output), indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
