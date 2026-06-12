from decimal import Decimal

import pytest

from marketpilot.configuration import load_environment_config, load_yaml_file
from marketpilot.fx import calculate_starting_cash_usd


def test_load_safe_paper_environment_config():
    config = load_environment_config("config/environments/paper.yaml")

    assert config.name == "paper"
    assert config.paper_trading_only is True
    assert config.fx_seed.trading_currency == "USD"
    assert config.fx_seed.display_currency == "NIS"
    assert config.fx_seed.starting_cash_usd.quantize(Decimal("0.01")) == Decimal("27027.03")


def test_yaml_loader_uses_safe_load_for_plain_mappings(tmp_path):
    path = tmp_path / "safe.yaml"
    path.write_text("paper_trading_only: true\n", encoding="utf-8")

    assert load_yaml_file(path) == {"paper_trading_only": True}


def test_unsafe_environment_config_fails(tmp_path):
    path = tmp_path / "unsafe.yaml"
    path.write_text(
        """
environment:
  name: paper
  paper_trading_only: false
  starting_budget_nis: 100000
  initial_usd_ils_rate: 3.7
  starting_cash_usd: 27027.027027
  trading_currency: USD
  display_currency: NIS
  fx_rate_timestamp: "2026-06-12T00:00:00Z"
  fx_rate_source: manual
""",
        encoding="utf-8",
    )

    with pytest.raises(Exception, match="paper_trading_only"):
        load_environment_config(path)


def test_fx_seed_calculation_is_deterministic():
    assert calculate_starting_cash_usd(100000, "3.7").quantize(Decimal("0.01")) == Decimal("27027.03")


@pytest.mark.parametrize(
    ("budget", "rate"),
    [(0, 3.7), (100000, 0), (-1, 3.7), (100000, -3.7)],
)
def test_invalid_fx_values_fail(budget, rate):
    with pytest.raises(ValueError, match="positive"):
        calculate_starting_cash_usd(budget, rate)


def test_secret_like_values_are_not_in_exception_text():
    secret_value = "very-private-token"
    with pytest.raises(Exception) as exc:
        load_yaml_file_from_text(
            f"""
paper_trading_only: true
api_token: {secret_value}
"""
        )

    assert secret_value not in str(exc.value)


def load_yaml_file_from_text(text: str):
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "config.yaml"
        path.write_text(text, encoding="utf-8")
        return load_yaml_file(path)
