import pytest

from marketpilot.product_modes import (
    ProductMode,
    assert_simulation_only_safety,
    parse_product_mode,
    product_mode_capabilities,
    product_mode_summary,
)


def test_simulation_only_is_default_and_core_mvp_mode():
    assert parse_product_mode(None) is ProductMode.SIMULATION_ONLY
    capabilities = product_mode_capabilities(ProductMode.SIMULATION_ONLY)

    assert capabilities.implemented_now is True
    assert capabilities.requires_quantconnect is False
    assert capabilities.allows_broker_credentials is False
    assert capabilities.allows_real_orders is False
    assert capabilities.dashboard_mutation_allowed is False
    assert capabilities.submits_quantconnect_orders is False


def test_qc_modes_are_not_implemented_now_and_are_not_real_money_modes():
    validation = product_mode_capabilities("qc_paper_validation")
    native = product_mode_capabilities("qc_native_algorithm")

    assert validation.implemented_now is False
    assert validation.requires_quantconnect is True
    assert validation.allows_real_orders is False
    assert validation.allows_broker_credentials is False
    assert native.implemented_now is False
    assert native.allows_real_orders is False


def test_product_mode_summary_is_safe_to_export():
    summary = product_mode_summary("simulation_only")

    assert summary["mode"] == "simulation_only"
    assert summary["paper_trading_only"] is True
    assert summary["requires_quantconnect"] is False
    assert "token" not in str(summary).lower()
    assert "password" not in str(summary).lower()


def test_unknown_product_mode_fails_closed():
    with pytest.raises(ValueError):
        parse_product_mode("live_money")


def test_assert_simulation_only_rejects_non_simulation_modes():
    with pytest.raises(RuntimeError, match="simulation_only"):
        assert_simulation_only_safety(mode="qc_paper_validation")

