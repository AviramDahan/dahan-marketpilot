"""Summarize Phase 16.2 burn-in evidence without leaking secrets."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_PHASE_DIR = Path(".planning/phases/16.2-end-to-end-uat-operational-burn-in")
REQUIRED_ITEMS = (
    "UAT-01",
    "UAT-02",
    "UAT-03",
    "UAT-04",
    "UAT-05",
    "UAT-06",
    "UAT-07",
    "UAT-08",
    "UAT-09",
    "OPS-01",
)
PASS_STATUS = "passed"
INCOMPLETE_STATUSES = {"not_run", "blocked_external_not_verified", "skipped"}
VALID_STATUSES = {PASS_STATUS, "failed", *INCOMPLETE_STATUSES}

SECRET_PATTERNS = (
    re.compile(r"\b\d{8,12}:[A-Za-z0-9_-]{25,}\b"),
    re.compile(r"\b[a-f0-9]{48,}\b", re.IGNORECASE),
    re.compile(r"(?i)(password|api[_-]?token|bot[_-]?token|secret)\s*[:=]\s*\S+"),
)


@dataclass(frozen=True)
class EvidenceRow:
    item: str
    status: str
    evidence: str
    next_action: str

    def to_json_dict(self) -> dict[str, str]:
        return {
            "item": self.item,
            "status": self.status,
            "evidence": self.evidence,
            "next_action": self.next_action,
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize Phase 16.2 burn-in evidence.")
    parser.add_argument("--phase-dir", type=Path, default=DEFAULT_PHASE_DIR)
    args = parser.parse_args(argv)

    result = build_report(args.phase_dir)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == PASS_STATUS else 2


def build_report(phase_dir: Path) -> dict[str, object]:
    uat_path = phase_dir / "16.2-UAT.md"
    ledger_path = phase_dir / "16.2-BURN-IN-LEDGER.md"
    readiness_path = phase_dir / "16.2-OPERATIONAL-READINESS.md"
    files = [uat_path, ledger_path, readiness_path]
    secret_hits = _secret_hits(files)
    rows = parse_uat_rows(uat_path) if uat_path.exists() else ()
    row_map = {row.item: row for row in rows}
    missing = [item for item in REQUIRED_ITEMS if item not in row_map]
    incomplete = [
        row.item
        for row in rows
        if row.item in REQUIRED_ITEMS and row.status != PASS_STATUS
    ]
    unknown_status = [
        row.item
        for row in rows
        if row.status not in VALID_STATUSES
    ]
    status = PASS_STATUS
    if secret_hits:
        status = "failed"
    elif missing or incomplete or unknown_status:
        status = "blocked_external_not_verified"
    return {
        "status": status,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "paper_trading_only": True,
        "required_total": len(REQUIRED_ITEMS),
        "passed_total": sum(1 for row in rows if row.item in REQUIRED_ITEMS and row.status == PASS_STATUS),
        "missing_items": missing,
        "incomplete_items": incomplete,
        "unknown_status_items": unknown_status,
        "secret_scan": {
            "status": "failed" if secret_hits else "passed",
            "hits": secret_hits,
        },
        "rows": [row.to_json_dict() for row in rows],
    }


def parse_uat_rows(path: Path) -> tuple[EvidenceRow, ...]:
    rows: list[EvidenceRow] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 5 or cells[0] in {"Item", "---"}:
            continue
        item, status, _provider, evidence, next_action = cells[:5]
        if item in REQUIRED_ITEMS:
            rows.append(
                EvidenceRow(
                    item=item,
                    status=status,
                    evidence=evidence,
                    next_action=next_action,
                )
            )
    return tuple(rows)


def _secret_hits(paths: list[Path]) -> list[dict[str, object]]:
    hits: list[dict[str, object]] = []
    for path in paths:
        if not path.exists():
            continue
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            for pattern in SECRET_PATTERNS:
                if pattern.search(line):
                    hits.append(
                        {
                            "path": str(path),
                            "line": line_number,
                            "pattern": pattern.pattern,
                        }
                    )
    return hits


if __name__ == "__main__":
    raise SystemExit(main())

