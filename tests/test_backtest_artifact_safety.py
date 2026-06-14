from pathlib import Path

from marketpilot.backtest_reports import ArtifactSource


ROOT = Path(__file__).resolve().parents[1]


def test_supported_artifact_labels_are_explicit():
    assert {source.value for source in ArtifactSource} == {
        "real_quantconnect",
        "fixture",
        "schema",
        "example",
        "not_run",
    }


def test_backtest_artifact_code_has_no_external_delivery_or_order_submission():
    combined = "\n".join(
        [
            (ROOT / "marketpilot" / "backtest_reports.py").read_text(encoding="utf-8").lower(),
            (ROOT / "marketpilot" / "validation.py").read_text(encoding="utf-8").lower(),
        ]
    )

    forbidden = ["submit_order", "market_order", "telegram", "brokerage", "api_key", "password"]
    assert not any(token in combined for token in forbidden)
