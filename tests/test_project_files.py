from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_required_foundation_files_exist():
    required = [
        "LICENSE",
        "NOTICE",
        "THIRD_PARTY_NOTICES.md",
        "DISCLAIMER.md",
        "README.md",
        "docs/safety.md",
        "docs/setup.md",
        "docs/configuration.md",
        "docs/testing.md",
        "docs/licensing.md",
        "docs/AI-COLLABORATION.md",
        "AGENTS.md",
    ]

    missing = [path for path in required if not (ROOT / path).is_file()]

    assert missing == []


def test_disclaimer_and_paper_guard_remain_visible():
    expected = "SIMULATED PAPER TRADING ONLY - NOT FINANCIAL ADVICE"

    assert expected in read("DISCLAIMER.md")
    assert expected in read("README.md")
    assert expected in read("docs/safety.md")
    assert "PAPER_TRADING_ONLY" in read("README.md")
    assert "PAPER_TRADING_ONLY" in read("docs/configuration.md")


def test_authority_and_read_only_rules_remain_visible():
    safety_doc = read("docs/safety.md")
    readme = read("README.md")

    assert "QuantConnect is the source of truth" in safety_doc
    assert "Render must remain read-only" in safety_doc
    assert "Telegram is a notification channel only" in safety_doc
    assert "Render is read-only" in readme
