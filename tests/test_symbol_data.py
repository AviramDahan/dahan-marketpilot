from marketpilot.data_quality import DataQualityStatus
from marketpilot.indicators import IndicatorResult, ReadinessStatus
from marketpilot.symbol_data import IndicatorReadiness, SymbolData, SymbolLifecycleState


def ready_result(name="EMA20", value=10.0):
    return IndicatorResult(name=name, status=ReadinessStatus.READY, value=value, required_points=20, available_points=20)


def test_symbol_data_ready_when_all_required_indicators_are_ready():
    symbol = SymbolData(
        symbol="MSFT",
        sector="Technology",
        data_quality_status=DataQualityStatus.ACCEPTED,
        indicators={"EMA20": ready_result("EMA20"), "RSI14": ready_result("RSI14", 55)},
    )

    assert symbol.readiness_for(("EMA20", "RSI14")) is IndicatorReadiness.READY
    assert symbol.future_signal_ready(("EMA20", "RSI14")) is True


def test_symbol_data_rejects_missing_unready_invalid_stale_nan_and_infinite_indicators():
    base = SymbolData("MSFT", "Technology", DataQualityStatus.ACCEPTED, {"EMA20": ready_result("EMA20")})
    assert base.readiness_for(("EMA20", "RSI14")) is IndicatorReadiness.MISSING

    unready = SymbolData("MSFT", "Technology", DataQualityStatus.ACCEPTED, {"EMA20": IndicatorResult("EMA20", ReadinessStatus.NOT_READY)})
    assert unready.readiness_for(("EMA20",)) is IndicatorReadiness.UNREADY

    invalid = SymbolData("MSFT", "Technology", DataQualityStatus.ACCEPTED, {"EMA20": IndicatorResult("EMA20", ReadinessStatus.INVALID)})
    assert invalid.readiness_for(("EMA20",)) is IndicatorReadiness.INVALID

    stale = SymbolData("MSFT", "Technology", DataQualityStatus.ACCEPTED, {"EMA20": ready_result("EMA20")})
    assert stale.readiness_for(("EMA20",), stale=True) is IndicatorReadiness.STALE

    nan_value = SymbolData("MSFT", "Technology", DataQualityStatus.ACCEPTED, {"EMA20": ready_result("EMA20", float("nan"))})
    assert nan_value.readiness_for(("EMA20",)) is IndicatorReadiness.INVALID

    infinite_value = SymbolData("MSFT", "Technology", DataQualityStatus.ACCEPTED, {"EMA20": ready_result("EMA20", float("inf"))})
    assert infinite_value.readiness_for(("EMA20",)) is IndicatorReadiness.INVALID


def test_symbol_data_cleanup_state_for_removed_security():
    symbol = SymbolData("MSFT", "Technology", DataQualityStatus.ACCEPTED, {"EMA20": ready_result("EMA20")})

    symbol.mark_removed()

    assert symbol.lifecycle_state is SymbolLifecycleState.REMOVED
    assert symbol.cleanup_complete is True
    assert symbol.indicators == {}
    assert symbol.readiness_for(("EMA20",)) is IndicatorReadiness.CLEANED_UP


def test_data_quality_rejection_composes_with_indicator_readiness():
    symbol = SymbolData("BAD", None, DataQualityStatus.REJECTED, {"EMA20": ready_result("EMA20")})

    assert symbol.readiness_for(("EMA20",)) is IndicatorReadiness.DATA_QUALITY_REJECTED
    assert symbol.future_signal_ready(("EMA20",)) is False

