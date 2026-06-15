from datetime import datetime, timezone

from marketpilot.runtime_orchestrator import RuntimeSetupMetadata, get_default_setup_registry
from marketpilot.setups import (
    RelativeStrengthInput,
    TrendPullbackInput,
    VolumeBreakoutInput,
    evaluate_relative_strength_leader,
    evaluate_trend_pullback,
    evaluate_volume_breakout,
)
from marketpilot.setups.base import SetupResult
from marketpilot.setups.trend_pullback import contract_result as trend_contract_result


def test_setup_package_exports_all_implemented_evaluators():
    assert callable(evaluate_trend_pullback)
    assert callable(evaluate_volume_breakout)
    assert callable(evaluate_relative_strength_leader)
    assert TrendPullbackInput.__name__ == "TrendPullbackInput"
    assert VolumeBreakoutInput.__name__ == "VolumeBreakoutInput"
    assert RelativeStrengthInput.__name__ == "RelativeStrengthInput"


def test_default_runtime_setup_registry_covers_all_implemented_setups():
    registry = get_default_setup_registry()

    assert tuple(registry) == ("trend_pullback", "volume_breakout", "relative_strength_leader")
    assert all(isinstance(item, RuntimeSetupMetadata) for item in registry.values())
    assert registry["trend_pullback"].setup_name == "trend_pullback"
    assert registry["volume_breakout"].setup_name == "volume_breakout"
    assert registry["relative_strength_leader"].setup_name == "relative_strength_leader"
    assert registry["trend_pullback"].evaluator is evaluate_trend_pullback
    assert registry["volume_breakout"].evaluator is evaluate_volume_breakout
    assert registry["relative_strength_leader"].evaluator is evaluate_relative_strength_leader


def test_setup_registry_metadata_is_evidence_only_and_does_not_enable_combined_swing():
    registry = get_default_setup_registry()

    assert "combined_swing" not in registry
    for metadata in registry.values():
        assert metadata.enabled is True
        assert metadata.paper_order_enabled is False
        assert metadata.creates_scores is False
        assert metadata.creates_orders is False
        assert metadata.supports_strategy_modes == (
            "daily_only",
            "daily_filter_4h_setup",
            "daily_filter_4h_setup_1h_optional",
        )


def test_registry_evaluators_preserve_setup_contract_result_shape():
    result = trend_contract_result("msft", datetime(2026, 6, 15, tzinfo=timezone.utc))

    assert isinstance(result, SetupResult)
    assert result.setup_name == "trend_pullback"
    assert result.symbol == "MSFT"
    assert not hasattr(result, "order")
    assert not hasattr(result, "paper_order")
    assert not hasattr(result, "portfolio_state")
