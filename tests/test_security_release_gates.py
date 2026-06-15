from __future__ import annotations

import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
SECRET_NAMES = (
    "QUANTCONNECT_USER_ID",
    "QUANTCONNECT_API_TOKEN",
    "QUANTCONNECT_PROJECT_ID",
    "DASHBOARD_HEALTH_URL",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
    "DASHBOARD_PASSWORD",
)
REVIEW_SECTIONS = (
    "Secret Handling",
    "Read-only Dashboard",
    "Real-money Trading",
    "QuantConnect Authority",
    "Action Supply Chain",
    "External not_run Handling",
    "Fake Performance And Profitability",
)


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _workflow(name: str) -> dict[str, object]:
    return yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8"))


def _workflow_texts() -> dict[str, str]:
    return {path.name: path.read_text(encoding="utf-8") for path in WORKFLOWS.glob("*.yml")}


def _lower_without_prohibited_sections(text: str) -> str:
    lowered = text.lower()
    return lowered.replace("prohibited action", "blocked action")


def test_security_review_covers_required_release_topics_and_status_taxonomy():
    review = _read("SECURITY_REVIEW.md")

    for section in REVIEW_SECTIONS:
        assert f"## {section}" in review

    for status in ("passed", "failed", "skipped", "not_run"):
        assert f"`{status}`" in review

    assert "SIMULATED PAPER TRADING ONLY - NOT FINANCIAL ADVICE" in review
    assert "df4cb1c069e1874edd31b4311f1884172cec0e10" in review
    assert "a309ff8b426b58ec0e2a45f0f869d46889d02405" in review
    assert "Lean package install is intentionally disabled" in review


def test_workflows_use_least_privilege_and_do_not_dump_secrets_or_urls():
    secret_value_shape = re.compile(r"(token|password|secret|api[_-]?key)\s*[:=]\s*['\"][^'\"]+['\"]", re.I)

    for name, text in _workflow_texts().items():
        workflow = _workflow(name)
        assert workflow["permissions"] == {"contents": "read"}
        assert "printenv" not in text
        assert "env |" not in text
        assert "set -x" not in text
        assert "echo \"$DASHBOARD_HEALTH_URL\"" not in text
        assert "echo \"$QUANTCONNECT_API_TOKEN\"" not in text
        assert "TELEGRAM_BOT_TOKEN:" not in text
        assert not secret_value_shape.search(text)


def test_external_workflows_record_unexecuted_status_and_avoid_mutation_paths():
    combined = "\n".join(_workflow_texts().values()).lower()
    external = _workflow_texts()["quantconnect.yml"] + _workflow_texts()["dashboard-health.yml"]

    assert "not_run" in external
    assert "skipped" in _read("SECURITY_REVIEW.md")

    forbidden_terms = (
        "lean cloud live deploy",
        "lean live",
        "market order",
        "submit order",
        "real broker",
        "leverage: true",
        "margin: true",
        "short selling: true",
        "options enabled",
        "futures enabled",
        "crypto enabled",
        "forex enabled",
        "curl -x post",
        "render deploy hook",
    )
    for term in forbidden_terms:
        assert term not in combined


def test_safety_and_testing_docs_cover_guarded_external_checks():
    combined = "\n".join([_read("docs/safety.md"), _read("docs/testing.md")])

    assert "CI/CD And Release Safety" in combined
    assert "Security Release Gates" in combined
    assert "GitHub Actions Secrets" in combined
    assert "not_run" in combined
    assert "skipped" in combined
    assert "Unexecuted external checks are not passed checks" in combined
    for secret_name in SECRET_NAMES:
        assert secret_name in combined
