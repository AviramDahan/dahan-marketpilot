from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERIFICATION_DOC = ROOT / "docs" / "quantconnect_verification.md"
LEAN_README = ROOT / "lean" / "README.md"


def test_quantconnect_verification_doc_cites_official_sources():
    text = VERIFICATION_DOC.read_text(encoding="utf-8")

    assert "https://www.quantconnect.com/docs/v2/lean-cli/api-reference" in text
    assert "https://www.quantconnect.com/docs/v2/cloud-platform/api-reference" in text
    assert "https://www.quantconnect.com/docs/v2/writing-algorithms/universes/equity/fundamental-universes" in text
    assert "https://www.quantconnect.com/docs/v2/writing-algorithms/indicators/key-concepts" in text


def test_quantconnect_verification_doc_enforces_no_credentials_or_cloud_runs():
    text = VERIFICATION_DOC.read_text(encoding="utf-8")

    assert "does not require or authorize" in text
    assert "Repository-stored credentials" in text
    assert "Cloud backtest execution" in text
    assert "Paper Trading deployment" in text
    assert "Live deployment" in text


def test_quantconnect_verification_doc_keeps_lean_build_optional():
    text = VERIFICATION_DOC.read_text(encoding="utf-8")
    lean_text = LEAN_README.read_text(encoding="utf-8")

    assert "lean build" in text
    assert "not run" in text
    assert "Do not claim a successful compile without executing it" in lean_text
    assert "no order" in lean_text


def test_quantconnect_verification_doc_does_not_claim_unrun_compile_success():
    text = VERIFICATION_DOC.read_text(encoding="utf-8").lower()
    lean_text = LEAN_README.read_text(encoding="utf-8").lower()

    forbidden_claims = [
        "lean build passed",
        "lean compile passed",
        "cloud backtest passed",
        "paper trading deployment passed",
    ]
    for claim in forbidden_claims:
        assert claim not in text
        assert claim not in lean_text

