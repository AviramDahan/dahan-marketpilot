"""Diagnose QuantConnect generic command dispatch with a no-order algorithm.

SIMULATED PAPER TRADING ONLY - NOT FINANCIAL ADVICE.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from marketpilot.qc_api import QCApiClient


ENABLE_ENV = "MARKETPILOT_QC_DISPATCH_PROBE_ENABLED"
REQUIRED_ENV = (
    "QUANTCONNECT_USER_ID",
    "QUANTCONNECT_API_TOKEN",
    "QC_PROJECT_ID",
)
DEPLOY_ENV = ("QC_NODE_ID", "QC_VERSION_ID")
SAFE_ID_ENV = ("QC_PROJECT_ID", "QC_DEPLOY_ID", "QC_COMPILE_ID", "QC_NODE_ID", "QC_VERSION_ID")
SECRET_MARKERS = ("TOKEN", "SECRET", "PASSWORD", "AUTH", "KEY")
PROBE_MARKER = "MARKETPILOT_DISPATCH_PROBE_RECEIVED"


def build_echo_algorithm() -> str:
    """Return a minimal Python QCAlgorithm that logs command receipt only."""
    return '''from AlgorithmImports import QCAlgorithm


class MarketPilotDispatchProbe(QCAlgorithm):
    def initialize(self):
        self.set_start_date(2026, 1, 1)
        self.set_end_date(2026, 1, 31)
        self.set_cash(100000)
        self.set_benchmark(lambda x: 1)
        self.debug("SIMULATED PAPER TRADING ONLY - NOT FINANCIAL ADVICE")
        self.debug("MARKETPILOT_DISPATCH_PROBE_READY")

    def on_command(self, data):
        correlation_id = self._safe_field(data, "correlation_id")
        command_type = self._safe_field(data, "command_type")
        self.debug(
            f"MARKETPILOT_DISPATCH_PROBE_RECEIVED "
            f"command_type={command_type} correlation_id={correlation_id}"
        )
        return True

    def _safe_field(self, data, name):
        if isinstance(data, dict):
            value = data.get(name)
        else:
            value = getattr(data, name, None)
        if value is None:
            return "missing"
        text = str(value)
        return text[:80]
'''


def build_generic_probe_command(*, now_utc: datetime | None = None) -> dict[str, object]:
    now = now_utc or datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%d%H%M%S")
    return {
        "command_type": "marketpilot_dispatch_probe",
        "correlation_id": f"qc-dispatch-probe-{stamp}",
        "paper_trading_only": True,
        "command_delivery_is_order_execution": False,
    }


def build_typed_probe_command(*, now_utc: datetime | None = None) -> dict[str, object]:
    command = build_generic_probe_command(now_utc=now_utc)
    return {"$type": "MarketPilotDispatchProbeCommand", **command}


def build_command(label: str, *, now_utc: datetime | None = None) -> dict[str, object]:
    if label == "generic_echo":
        return build_generic_probe_command(now_utc=now_utc)
    if label == "flat_typed_echo":
        return build_typed_probe_command(now_utc=now_utc)
    raise ValueError(f"unsupported command label: {label}")


def summarize_env() -> dict[str, str]:
    summary: dict[str, str] = {}
    for name in REQUIRED_ENV + DEPLOY_ENV + SAFE_ID_ENV:
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


def run_probe(
    *,
    command_label: str,
    dry_run: bool,
    file_name: str,
    restore_original: bool,
    deploy: bool,
    polls: int,
    poll_seconds: int,
    compile_polls: int,
    compile_poll_seconds: int,
) -> dict[str, object]:
    _require_enabled()
    now = datetime.now(timezone.utc)
    command = build_command(command_label, now_utc=now)
    algorithm = build_echo_algorithm()
    result: dict[str, object] = {
        "status": "dry_run" if dry_run else "running",
        "checked_at_utc": now.isoformat(),
        "paper_trading_only": True,
        "probe_marker": PROBE_MARKER,
        "command_label": command_label,
        "file_name": file_name,
        "restore_original": restore_original,
        "deploy": deploy,
        "environment": summarize_env(),
        "command_preview": sanitize(command),
        "algorithm_preview": sanitize(algorithm),
    }
    if dry_run:
        return result

    project_id = _read_int_env("QC_PROJECT_ID")
    client = QCApiClient()
    original_content = ""
    original_read = client.read_project_file(project_id=project_id, name=file_name)
    original_content = _extract_project_file_content(original_read, file_name)
    result["original_file_read"] = sanitize(_summarize_project_file_read(original_read))

    compile_id = ""
    try:
        result["file_update_success"] = client.update_project_file_content(
            project_id=project_id,
            name=file_name,
            content=algorithm,
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
    finally:
        if restore_original and original_content:
            result["restore_original_success"] = client.update_project_file_content(
                project_id=project_id,
                name=file_name,
                content=original_content,
            )

    if deploy:
        deploy_response = client.create_live_algorithm(
            project_id=project_id,
            compile_id=compile_id or _read_env("QC_COMPILE_ID"),
            node_id=_read_env("QC_NODE_ID"),
            version_id=_read_env("QC_VERSION_ID"),
            data_providers={"QuantConnectBrokerage": {"id": "QuantConnectBrokerage"}},
        )
        result["deploy_response"] = sanitize(deploy_response)
        deploy_id = _extract_deploy_id(deploy_response) or os.environ.get("QC_DEPLOY_ID", "").strip()
    else:
        deploy_id = _read_env("QC_DEPLOY_ID")

    result["deploy_id"] = deploy_id
    result["command_api_success"] = client.create_live_command(project_id=project_id, command=command)
    observations: list[dict[str, object]] = []
    for index in range(polls):
        if index:
            time.sleep(poll_seconds)
        logs = client.read_live_logs(project_id=project_id, deploy_id=deploy_id)
        live_logs = logs.get("LiveLogs") or logs.get("logs") or []
        observations.append(
            {
                "poll": index,
                "live_log_count": len(live_logs) if isinstance(live_logs, list) else 0,
                "probe_marker_observed": PROBE_MARKER in str(live_logs),
                "live_logs_tail": sanitize(live_logs[-10:] if isinstance(live_logs, list) else live_logs),
            }
        )
        if observations[-1]["probe_marker_observed"]:
            break

    result["observations"] = observations
    result["status"] = (
        "generic_command_dispatch_observed"
        if any(obs.get("probe_marker_observed") for obs in observations)
        else "api_accepted_no_generic_dispatch_observed"
    )
    return result


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


def _summarize_project_file_read(response: Mapping[str, object]) -> dict[str, object]:
    content = _extract_project_file_content(response, "")
    summary = dict(response)
    summary.pop("content", None)
    summary.pop("Content", None)
    summary["content_length"] = len(content)
    return summary


def _extract_deploy_id(response: Mapping[str, object]) -> str:
    for key in ("deployId", "DeployId", "algorithmId", "AlgorithmId", "liveId"):
        value = response.get(key)
        if value:
            return str(value)
    return ""


def _require_enabled() -> None:
    if os.environ.get(ENABLE_ENV, "").strip() != "1":
        raise SystemExit(f"Set {ENABLE_ENV}=1 to run this paper-only dispatch probe.")


def _read_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def _read_int_env(name: str) -> int:
    return int(_read_env(name))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--command-label", choices=("generic_echo", "flat_typed_echo"), default="generic_echo")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--file-name", default="main.py")
    parser.add_argument("--no-restore-original", action="store_true")
    parser.add_argument("--skip-deploy", action="store_true")
    parser.add_argument("--polls", type=int, default=12)
    parser.add_argument("--poll-seconds", type=int, default=5)
    parser.add_argument("--compile-polls", type=int, default=12)
    parser.add_argument("--compile-poll-seconds", type=int, default=5)
    args = parser.parse_args(argv)

    output = run_probe(
        command_label=args.command_label,
        dry_run=args.dry_run,
        file_name=args.file_name,
        restore_original=not args.no_restore_original,
        deploy=not args.skip_deploy,
        polls=args.polls,
        poll_seconds=args.poll_seconds,
        compile_polls=args.compile_polls,
        compile_poll_seconds=args.compile_poll_seconds,
    )
    print(json.dumps(sanitize(output), indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
