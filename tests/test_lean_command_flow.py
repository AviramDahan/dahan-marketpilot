from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from marketpilot.lean_command_receiver import (
    normalize_marketpilot_command,
    validate_marketpilot_command,
)


ROOT = Path(__file__).resolve().parents[1]
LEAN_MAIN = ROOT / "lean" / "main.py"
NOW = datetime(2026, 6, 16, 14, 30, tzinfo=timezone.utc)


def _payload(**overrides):
    payload = {
        "command_type": "marketpilot_signal",
        "correlation_id": "corr-001",
        "signal_id": "sig-001",
        "idempotency_key": "order-intent-001",
        "symbol": "MSFT",
        "quantity": 12,
        "signal_time_utc": "2026-06-16T14:20:00+00:00",
        "expires_at_utc": "2026-06-16T14:40:00+00:00",
        "strategy_mode": "daily_only",
        "primary_setup": "relative_strength_leader",
        "paper_trading_only": True,
        "command_delivery_is_order_execution": False,
    }
    payload.update(overrides)
    return payload


def test_normalize_marketpilot_command_accepts_dict_payload():
    command = normalize_marketpilot_command(_payload())

    assert command.accepted is True
    assert command.command is not None
    assert command.command.symbol == "MSFT"
    assert command.command.quantity == 12
    assert command.command.expires_at_utc == datetime(2026, 6, 16, 14, 40, tzinfo=timezone.utc)


def test_normalize_marketpilot_command_accepts_attribute_payload():
    command = normalize_marketpilot_command(SimpleNamespace(**_payload(symbol="AAPL")))

    assert command.accepted is True
    assert command.command is not None
    assert command.command.symbol == "AAPL"


def test_normalize_marketpilot_command_accepts_pascal_case_attribute_payload():
    payload = SimpleNamespace(
        CommandType="marketpilot_signal",
        CorrelationId="corr-001",
        SignalId="sig-001",
        IdempotencyKey="order-intent-001",
        Symbol="MSFT",
        Quantity=12,
        SignalTimeUtc="2026-06-16T14:20:00+00:00",
        ExpiresAtUtc="2026-06-16T14:40:00+00:00",
        StrategyMode="daily_only",
        PrimarySetup="relative_strength_leader",
        PaperTradingOnly=True,
        CommandDeliveryIsOrderExecution=False,
    )

    command = normalize_marketpilot_command(payload)

    assert command.accepted is True
    assert command.command is not None
    assert command.command.symbol == "MSFT"


def test_normalize_marketpilot_command_accepts_parameters_envelope():
    payload = {
        "$type": "MarketPilotSignalCommand",
        "parameters": _payload(symbol="SPY"),
    }

    command = normalize_marketpilot_command(payload)

    assert command.accepted is True
    assert command.command is not None
    assert command.command.symbol == "SPY"


def test_normalize_marketpilot_command_accepts_flat_typed_payload():
    payload = {"$type": "MarketPilotSignalCommand", **_payload(symbol="SPY")}

    command = normalize_marketpilot_command(payload)

    assert command.accepted is True
    assert command.command is not None
    assert command.command.symbol == "SPY"


def test_normalize_marketpilot_command_accepts_nested_marketpilot_signal_payload():
    payload = {"marketpilot_signal": _payload(symbol="QQQ")}

    command = normalize_marketpilot_command(payload)

    assert command.accepted is True
    assert command.command is not None
    assert command.command.symbol == "QQQ"


def test_normalize_marketpilot_command_rejects_unsafe_typed_order_probe():
    payload = {
        "$type": "OrderCommand",
        "symbol": {"value": "SPY"},
        "order_type": "market",
        "quantity": 1,
    }

    command = normalize_marketpilot_command(payload)

    assert command.accepted is False
    assert command.reason == "unsupported_field_order_type"


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("command_type", "external_order", "unsupported_command_type"),
        ("signal_id", "", "missing_signal_id"),
        ("expires_at_utc", "not-a-time", "malformed_expires_at_utc"),
        ("signal_time_utc", "2026-06-16T14:20:00", "naive_signal_time_utc"),
        ("quantity", 0, "non_positive_quantity"),
        ("quantity", 1.5, "non_integer_quantity"),
        ("symbol", "BTC/USD", "unsupported_symbol"),
        ("paper_trading_only", False, "non_paper_command"),
    ],
)
def test_normalize_marketpilot_command_rejects_malformed_or_unsupported_payloads(field, value, reason):
    result = normalize_marketpilot_command(_payload(**{field: value}))

    assert result.accepted is False
    assert result.reason == reason
    assert result.command is None


def test_validate_marketpilot_command_accepts_fresh_non_duplicate_command():
    normalized = normalize_marketpilot_command(_payload())
    seen_keys: set[str] = set()

    decision = validate_marketpilot_command(normalized.command, seen_idempotency_keys=seen_keys, now_utc=NOW)

    assert decision.accepted is True
    assert decision.reason == "accepted"
    assert decision.symbol == "MSFT"
    assert decision.quantity == 12
    assert decision.tag == "mp:sig-001:order-intent-001"
    assert seen_keys == {"order-intent-001"}


def test_validate_marketpilot_command_rejects_stale_command_before_seen_key_mutates():
    normalized = normalize_marketpilot_command(
        _payload(expires_at_utc="2026-06-16T14:29:59+00:00")
    )
    seen_keys: set[str] = set()

    decision = validate_marketpilot_command(normalized.command, seen_idempotency_keys=seen_keys, now_utc=NOW)

    assert decision.accepted is False
    assert decision.reason == "expired_signal"
    assert decision.tag is None
    assert seen_keys == set()


def test_validate_marketpilot_command_rejects_duplicate_before_order_placement():
    normalized = normalize_marketpilot_command(_payload())
    seen_keys = {"order-intent-001"}

    decision = validate_marketpilot_command(normalized.command, seen_idempotency_keys=seen_keys, now_utc=NOW)

    assert decision.accepted is False
    assert decision.reason == "duplicate_idempotency_key"
    assert decision.symbol == "MSFT"
    assert decision.quantity == 12
    assert decision.tag is None


def _load_lean_main(monkeypatch):
    class FakeSchedule:
        def __init__(self):
            self.calls = []

        def on(self, date_rule, time_rule, callback):
            self.calls.append((date_rule, time_rule, callback))

    class FakeDateRules:
        def every_day(self):
            return "every_day"

    class FakeTimeRules:
        def every(self, interval):
            return ("every", interval)

    class FakeQCAlgorithm:
        parameter_values = {}

        def set_start_date(self, *args):
            self.start_date = args

        def set_end_date(self, *args):
            self.end_date = args

        def set_cash(self, cash):
            self.cash = cash

        def add_equity(self, symbol, resolution):
            self.equities = getattr(self, "equities", [])
            self.equities.append((symbol, resolution))
            return SimpleNamespace(Symbol=symbol)

        def add_universe(self, selector):
            self.universe_selector = selector

        def get_parameter(self, name):
            return self.parameter_values.get(name, "")

        def debug(self, message):
            self.debug_messages = getattr(self, "debug_messages", [])
            self.debug_messages.append(message)

        def market_order(self, symbol, quantity, tag=None):
            self.market_orders = getattr(self, "market_orders", [])
            self.market_orders.append({"symbol": symbol, "quantity": quantity, "tag": tag})
            return SimpleNamespace(order_id=len(self.market_orders), symbol=symbol, quantity=quantity, tag=tag)

    fake_algorithm_imports = SimpleNamespace(
        QCAlgorithm=FakeQCAlgorithm,
        Resolution=SimpleNamespace(DAILY="Daily"),
    )
    monkeypatch.setitem(sys.modules, "AlgorithmImports", fake_algorithm_imports)
    module_name = "lean_main_test_module"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, LEAN_MAIN)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    module.FakeSchedule = FakeSchedule
    module.FakeDateRules = FakeDateRules
    module.FakeTimeRules = FakeTimeRules
    return module


def _algorithm(monkeypatch):
    module = _load_lean_main(monkeypatch)
    algorithm = module.DahanMarketPilotRuntime()
    algorithm.time = NOW
    algorithm.initialize()
    return algorithm


def test_initialize_schedules_object_store_polling_when_key_parameter_exists(monkeypatch):
    module = _load_lean_main(monkeypatch)
    base = module.DahanMarketPilotRuntime.__mro__[1]
    base.parameter_values = {
        "marketpilot_object_store_signal_key": "123/marketpilot/signals/smoke.json"
    }
    algorithm = module.DahanMarketPilotRuntime()
    algorithm.schedule = module.FakeSchedule()
    algorithm.date_rules = module.FakeDateRules()
    algorithm.time_rules = module.FakeTimeRules()

    algorithm.initialize()

    assert algorithm.marketpilot_object_store_signal_key == "123/marketpilot/signals/smoke.json"
    assert len(algorithm.schedule.calls) == 1
    assert algorithm.schedule.calls[0][0] == "every_day"
    assert algorithm.schedule.calls[0][2] == algorithm.poll_marketpilot_object_store_signal
    base.parameter_values = {}


def test_initialize_creates_command_idempotency_and_order_event_evidence(monkeypatch):
    algorithm = _algorithm(monkeypatch)

    assert algorithm.marketpilot_seen_command_keys == set()
    assert algorithm.latest_command_receipt_evidence is None
    assert algorithm.latest_object_store_receipt_evidence is None
    assert algorithm.latest_order_event_evidence is None


def test_on_command_accepts_fresh_marketpilot_signal(monkeypatch):
    algorithm = _algorithm(monkeypatch)

    accepted = algorithm.on_command(_payload())

    assert accepted is True
    assert algorithm.market_orders == [
        {"symbol": "MSFT", "quantity": 12, "tag": "mp:sig-001:order-intent-001"}
    ]
    assert algorithm.marketpilot_seen_command_keys == {"order-intent-001"}
    assert algorithm.latest_command_receipt_evidence == {
        "received": True,
        "payload_kind": "dict",
        "has_command_type": True,
        "has_type": False,
    }


def test_on_command_accepts_quantconnect_capitalized_keys(monkeypatch):
    algorithm = _algorithm(monkeypatch)
    payload = {
        "Command_type": "marketpilot_signal",
        "Correlation_id": "corr-001",
        "Signal_id": "sig-001",
        "Idempotency_key": "order-intent-qc-case",
        "Symbol": "MSFT",
        "Quantity": 12,
        "Signal_time_utc": "2026-06-16T14:20:00+00:00",
        "Expires_at_utc": "2026-06-16T14:40:00+00:00",
        "Paper_trading_only": True,
    }

    accepted = algorithm.on_command(payload)

    assert accepted is True
    assert algorithm.market_orders == [
        {"symbol": "MSFT", "quantity": 12, "tag": "mp:sig-001:order-intent-qc-case"}
    ]


def test_on_command_accepts_quantconnect_payload_data_envelope(monkeypatch):
    algorithm = _algorithm(monkeypatch)
    payload = {
        "PayloadData": json.dumps(
            _payload(idempotency_key="order-intent-qc-envelope")
        )
    }

    accepted = algorithm.on_command(payload)

    assert accepted is True
    assert algorithm.market_orders == [
        {"symbol": "MSFT", "quantity": 12, "tag": "mp:sig-001:order-intent-qc-envelope"}
    ]


def test_on_command_accepts_quantconnect_payload_data_object_envelope(monkeypatch):
    algorithm = _algorithm(monkeypatch)

    class PayloadObject:
        def __init__(self, **values):
            for key, value in values.items():
                setattr(self, key, value)

    payload = {
        "PayloadData": PayloadObject(
            **_payload(idempotency_key="order-intent-qc-object-envelope")
        )
    }

    accepted = algorithm.on_command(payload)

    assert accepted is True
    assert algorithm.market_orders == [
        {
            "symbol": "MSFT",
            "quantity": 12,
            "tag": "mp:sig-001:order-intent-qc-object-envelope",
        }
    ]


@pytest.mark.parametrize(
    "payload",
    [
        _payload(expires_at_utc="2026-06-16T14:29:59+00:00"),
        _payload(idempotency_key="already-seen"),
        _payload(command_type="unsupported"),
        _payload(signal_time_utc="2026-06-16T14:20:00"),
        _payload(paper_trading_only=False),
    ],
)
def test_on_command_rejects_unsafe_commands_without_order(monkeypatch, payload):
    algorithm = _algorithm(monkeypatch)
    algorithm.marketpilot_seen_command_keys.add("already-seen")

    accepted = algorithm.on_command(payload)

    assert accepted is False
    assert getattr(algorithm, "market_orders", []) == []


def test_on_command_accepts_attribute_payload_once(monkeypatch):
    algorithm = _algorithm(monkeypatch)
    payload = SimpleNamespace(**_payload(symbol="AAPL", idempotency_key="order-intent-002"))

    assert algorithm.on_command(payload) is True
    assert algorithm.on_command(payload) is False
    assert algorithm.market_orders == [
        {"symbol": "AAPL", "quantity": 12, "tag": "mp:sig-001:order-intent-002"}
    ]


def test_on_order_event_records_sanitized_trace_evidence(monkeypatch):
    algorithm = _algorithm(monkeypatch)
    algorithm.transactions = SimpleNamespace(
        get_order_by_id=lambda order_id: SimpleNamespace(tag="mp:sig-001:order-intent-001")
    )
    order_event = SimpleNamespace(
        order_id=42,
        status="Filled",
        fill_quantity=12,
        fill_price=234.56,
        message="paper fill event",
    )

    result = algorithm.on_order_event(order_event)

    assert result == algorithm.latest_order_event_evidence
    assert result == {
        "order_id": 42,
        "status": "Filled",
        "fill_quantity": 12,
        "fill_price": 234.56,
        "tag": "mp:sig-001:order-intent-001",
        "signal_id": "sig-001",
        "idempotency_key": "order-intent-001",
    }
    assert "message" not in result


class FakeObjectStore:
    def __init__(self, payloads):
        self.payloads = payloads
        self.clear_called = False

    def clear(self):
        self.clear_called = True

    def contains_key(self, key):
        return key in self.payloads

    def read(self, key):
        return self.payloads[key]


def test_object_store_signal_poll_accepts_fresh_payload_through_shared_validation(monkeypatch):
    algorithm = _algorithm(monkeypatch)
    key = "123/marketpilot/signals/smoke.json"
    algorithm.marketpilot_object_store_signal_key = key
    algorithm.object_store = FakeObjectStore({key: json.dumps(_payload(idempotency_key="object-store-001"))})

    accepted = algorithm.poll_marketpilot_object_store_signal()

    assert accepted is True
    assert algorithm.object_store.clear_called is True
    assert algorithm.latest_object_store_receipt_evidence == {
        "received": True,
        "key": key,
        "payload_kind": "dict",
        "has_command_type": True,
    }
    assert algorithm.market_orders == [
        {"symbol": "MSFT", "quantity": 12, "tag": "mp:sig-001:object-store-001"}
    ]
    assert algorithm.poll_marketpilot_object_store_signal() is False
    assert len(algorithm.market_orders) == 1


def test_object_store_signal_waits_for_tradeable_price_before_processing(monkeypatch):
    algorithm = _algorithm(monkeypatch)
    key = "123/marketpilot/signals/wait-for-price.json"
    algorithm.marketpilot_object_store_signal_key = key
    algorithm.object_store = FakeObjectStore({key: json.dumps(_payload(idempotency_key="object-store-wait"))})
    algorithm.securities = {"MSFT": SimpleNamespace(has_data=False, price=0)}

    accepted = algorithm.poll_marketpilot_object_store_signal()

    assert accepted is False
    assert key not in algorithm.marketpilot_processed_object_store_keys
    assert algorithm.marketpilot_seen_command_keys == set()
    assert getattr(algorithm, "market_orders", []) == []
    assert algorithm.latest_command_pending_evidence == {
        "pending": True,
        "reason": "symbol_price_not_ready",
        "symbol": "MSFT",
        "source": "object_store",
    }

    algorithm.securities["MSFT"] = SimpleNamespace(has_data=True, price=250.0)

    accepted = algorithm.poll_marketpilot_object_store_signal()

    assert accepted is True
    assert key in algorithm.marketpilot_processed_object_store_keys
    assert algorithm.market_orders == [
        {"symbol": "MSFT", "quantity": 12, "tag": "mp:sig-001:object-store-wait"}
    ]


def test_object_store_signal_poll_rejects_stale_without_order(monkeypatch):
    algorithm = _algorithm(monkeypatch)
    key = "123/marketpilot/signals/stale.json"
    algorithm.marketpilot_object_store_signal_key = key
    algorithm.object_store = FakeObjectStore(
        {key: json.dumps(_payload(expires_at_utc="2026-06-16T14:29:59+00:00"))}
    )

    accepted = algorithm.poll_marketpilot_object_store_signal()

    assert accepted is False
    assert getattr(algorithm, "market_orders", []) == []
    assert algorithm.latest_command_rejection_evidence["reason"] == "expired_signal"
    assert algorithm.latest_command_rejection_evidence["source"] == "object_store"


def test_object_store_signal_poll_rejects_malformed_json_once(monkeypatch):
    algorithm = _algorithm(monkeypatch)
    key = "123/marketpilot/signals/malformed.json"
    algorithm.marketpilot_object_store_signal_key = key
    algorithm.object_store = FakeObjectStore({key: "{not-json"})

    accepted = algorithm.poll_marketpilot_object_store_signal()

    assert accepted is False
    assert getattr(algorithm, "market_orders", []) == []
    assert algorithm.latest_object_store_receipt_evidence == {
        "received": True,
        "key": key,
        "reason": "malformed_object_store_json",
    }
    assert algorithm.poll_marketpilot_object_store_signal() is False
