from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RELEASE_DOCS = (
    "docs/release.md",
    "SECURITY_REVIEW.md",
    "docs/operations.md",
    "docs/troubleshooting.md",
    "docs/safety.md",
    "docs/testing.md",
    "docs/licensing.md",
)


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_release_doc_traces_all_phase_10_requirements():
    text = _read("docs/release.md")

    for requirement in ("CI-01", "CI-02", "CI-03", "CI-04", "CI-05", "CI-06"):
        assert f"| {requirement} |" in text

    assert "Requirement Traceability" in text
    assert "Release Evidence" in text


def test_release_doc_records_status_vocabulary_and_required_commands():
    text = _read("docs/release.md")

    for status in ("`passed`", "`failed`", "`skipped`", "`not_run`"):
        assert status in text

    assert "python -m pytest -q" in text
    assert "git status --short --branch" in text


def test_release_doc_links_required_handoff_artifacts():
    text = _read("docs/release.md")

    for artifact in (
        "SECURITY_REVIEW.md",
        "docs/operations.md",
        "docs/troubleshooting.md",
        "NOTICE",
        "THIRD_PARTY_NOTICES.md",
        "DISCLAIMER.md",
        "LICENSE",
    ):
        assert artifact in text


def test_release_docs_reject_fake_performance_and_external_false_passes():
    combined = "\n".join(_read(path) for path in RELEASE_DOCS).lower()

    required_boundaries = (
        "fake performance",
        "fake backtest",
        "fake paper",
        "fake portfolio",
        "unverified profitability",
        "unexecuted external checks are not passed checks",
    )
    for boundary in required_boundaries:
        assert boundary in combined

    forbidden_claims = (
        "guaranteed returns",
        "risk-free profit",
        "external checks passed without running",
        "skipped external checks passed",
        "not_run external checks passed",
    )
    for claim in forbidden_claims:
        assert claim not in combined


def test_licensing_doc_requires_release_attribution_review():
    text = _read("docs/licensing.md")

    assert "Release Attribution Review" in text
    assert "NOTICE" in text
    assert "THIRD_PARTY_NOTICES.md" in text
    assert "direct-copy" in text
    assert "substantially adapted third-party source" in text
