import json

from scripts import phase16_2_evidence_report


def test_report_blocks_when_rows_are_not_run(tmp_path, capsys):
    phase_dir = tmp_path
    (phase_dir / "16.2-UAT.md").write_text(
        """| Item | Status | Provider | Evidence | Next Action |
|---|---|---|---|---|
| UAT-01 | not_run | QuantConnect | None yet | Observe order authority |
| UAT-02 | not_run | Render | None yet | Observe heartbeat |
| UAT-03 | not_run | Render | None yet | Restart worker |
| UAT-04 | not_run | Render Key Value | None yet | Exercise lock |
| UAT-05 | not_run | Dashboard | None yet | Observe stale state |
| UAT-06 | not_run | QuantConnect | None yet | Inject fake failure |
| UAT-07 | not_run | Telegram | None yet | Inject fake failure |
| UAT-08 | not_run | Render | None yet | Observe two sessions |
| UAT-09 | not_run | Planning | None yet | Final report |
| OPS-01 | not_run | Governance | None yet | Close all gates |
""",
        encoding="utf-8",
    )
    (phase_dir / "16.2-BURN-IN-LEDGER.md").write_text("# Ledger\n", encoding="utf-8")
    (phase_dir / "16.2-OPERATIONAL-READINESS.md").write_text("# Report\n", encoding="utf-8")

    result = phase16_2_evidence_report.main(["--phase-dir", str(phase_dir)])

    output = json.loads(capsys.readouterr().out)
    assert result == 2
    assert output["status"] == "blocked_external_not_verified"
    assert output["passed_total"] == 0
    assert output["required_total"] == 10
    assert output["secret_scan"]["status"] == "passed"


def test_report_passes_only_when_all_required_rows_pass(tmp_path, capsys):
    rows = "\n".join(
        f"| {item} | passed | external | Sanitized evidence | Complete |"
        for item in phase16_2_evidence_report.REQUIRED_ITEMS
    )
    (tmp_path / "16.2-UAT.md").write_text(
        f"| Item | Status | Provider | Evidence | Next Action |\n|---|---|---|---|---|\n{rows}\n",
        encoding="utf-8",
    )
    (tmp_path / "16.2-BURN-IN-LEDGER.md").write_text("# Ledger\n", encoding="utf-8")
    (tmp_path / "16.2-OPERATIONAL-READINESS.md").write_text("# Report\n", encoding="utf-8")

    result = phase16_2_evidence_report.main(["--phase-dir", str(tmp_path)])

    output = json.loads(capsys.readouterr().out)
    assert result == 0
    assert output["status"] == "passed"
    assert output["passed_total"] == 10


def test_report_fails_when_secret_like_value_is_recorded(tmp_path, capsys):
    rows = "\n".join(
        f"| {item} | passed | external | Sanitized evidence | Complete |"
        for item in phase16_2_evidence_report.REQUIRED_ITEMS
    )
    (tmp_path / "16.2-UAT.md").write_text(
        f"| Item | Status | Provider | Evidence | Next Action |\n|---|---|---|---|---|\n{rows}\n",
        encoding="utf-8",
    )
    (tmp_path / "16.2-BURN-IN-LEDGER.md").write_text(
        "bot_token=1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcde\n",
        encoding="utf-8",
    )
    (tmp_path / "16.2-OPERATIONAL-READINESS.md").write_text("# Report\n", encoding="utf-8")

    result = phase16_2_evidence_report.main(["--phase-dir", str(tmp_path)])

    output = json.loads(capsys.readouterr().out)
    assert result == 2
    assert output["status"] == "failed"
    assert output["secret_scan"]["status"] == "failed"

