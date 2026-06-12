from decimal import Decimal

import pytest

from marketpilot.models import (
    CurrencyCode,
    FxSeed,
    Money,
    ReadOnlyStatus,
    SafetyStatus,
    TradingMode,
    ValidationIssue,
)


def test_money_accepts_positive_supported_currency():
    money = Money.from_value("123.45", "USD")

    assert money.amount == Decimal("123.45")
    assert money.currency is CurrencyCode.USD
    assert money.format_public() == "123.45 USD"


@pytest.mark.parametrize("amount", ["0", "-1", 0, -10])
def test_money_rejects_non_positive_amount(amount):
    with pytest.raises(ValueError, match="positive"):
        Money.from_value(amount, "USD")


def test_money_rejects_unsupported_currency():
    with pytest.raises(ValueError, match="USD or NIS"):
        Money.from_value(100, "EUR")


def test_fx_seed_model_calculates_starting_cash():
    seed = FxSeed.create(
        starting_budget_nis=100000,
        initial_usd_ils_rate="3.7",
        fx_rate_timestamp="2026-06-12T00:00:00Z",
        fx_rate_source="manual launch seed",
    )

    assert seed.starting_budget.currency is CurrencyCode.NIS
    assert seed.starting_cash.currency is CurrencyCode.USD
    assert seed.starting_cash.amount.quantize(Decimal("0.01")) == Decimal("27027.03")


def test_safety_status_requires_paper_mode():
    SafetyStatus(paper_trading_only=True, mode=TradingMode.PAPER).validate()

    with pytest.raises(ValueError, match="paper-only"):
        SafetyStatus(paper_trading_only=False, mode=TradingMode.PAPER).validate()


def test_read_only_status_requires_static_phase_1_surface():
    ReadOnlyStatus(read_only=True, no_live_data_connected=True).validate()

    with pytest.raises(ValueError, match="read-only"):
        ReadOnlyStatus(read_only=False, no_live_data_connected=True).validate()


def test_validation_issue_public_message_redacts_secret_like_text():
    issue = ValidationIssue(
        path="settings.api_key",
        code="unsafe",
        message="secret token must not appear",
    )

    public_message = issue.public_message()

    assert "api_key" not in public_message
    assert "secret" not in public_message
    assert "token" not in public_message
    assert "[redacted]" in public_message
