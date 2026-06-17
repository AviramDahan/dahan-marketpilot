import json
from datetime import datetime, timedelta, timezone

from AlgorithmImports import QCAlgorithm, Resolution

from marketpilot.lean_command_receiver import (
    normalize_marketpilot_command,
    validate_marketpilot_command,
)
from marketpilot.lean_bridge import (
    LeanRuntimeBridge,
    initialize_runtime_bridge,
    map_quantconnect_bar_to_completed_bar,
)
from marketpilot.paper_command_models import parse_order_tag
from marketpilot.timeframes import BarTimeframe


class DahanMarketPilotRuntime(QCAlgorithm):
    """Thin QuantConnect adapter for the MarketPilot runtime bridge."""

    MARKETPILOT_OBJECT_STORE_SIGNAL_KEY = ""

    def initialize(self):
        self.set_start_date(2026, 1, 1)
        self.set_end_date(2026, 1, 31)
        self.set_cash(27027.03)

        self.runtime_bridge: LeanRuntimeBridge = initialize_runtime_bridge()
        self.latest_runtime_result = None
        self.latest_dashboard_export_evidence = self.runtime_bridge.export_dashboard_evidence(None)
        self.marketpilot_seen_command_keys = set()
        self.latest_command_receipt_evidence = None
        self.latest_object_store_receipt_evidence = None
        self.latest_order_event_evidence = None
        self.latest_command_rejection_evidence = None
        self.latest_command_pending_evidence = None
        self.marketpilot_object_store_signal_key = self._marketpilot_object_store_signal_key()
        self.marketpilot_processed_object_store_keys = set()

        self.add_equity("SPY", Resolution.DAILY)
        self.add_equity("QQQ", Resolution.DAILY)
        self.add_universe(self.select_dynamic_universe)
        self._schedule_marketpilot_object_store_polling()

        self.debug("SIMULATED PAPER TRADING ONLY - NOT FINANCIAL ADVICE")

    def select_dynamic_universe(self, coarse):
        return self.runtime_bridge.select_dynamic_universe(coarse)

    def on_securities_changed(self, changes):
        return self.runtime_bridge.on_securities_changed(changes)

    def on_completed_daily_bar(self, sender, bar):
        completed_bar = map_quantconnect_bar_to_completed_bar(
            bar,
            timeframe=BarTimeframe.DAILY,
            exchange_timezone="America/New_York",
            source_resolution="daily",
            is_closed=True,
        )
        symbol = getattr(bar, "Symbol", "")
        result = self.runtime_bridge.on_completed_bar(
            symbol=symbol,
            bar=completed_bar,
            setup_results=(),
            correlation_id=f"lean-{symbol}-{completed_bar.time.isoformat()}",
        )
        self.latest_runtime_result = result
        self.latest_dashboard_export_evidence = self.runtime_bridge.export_dashboard_evidence(result)
        return result

    def on_command(self, data):
        self.latest_command_receipt_evidence = {
            "received": True,
            "payload_kind": type(data).__name__,
            "has_command_type": _has_safe_field(data, "command_type", "CommandType"),
            "has_type": _has_safe_field(data, "$type", "type", "Type"),
        }
        self.debug("MarketPilot command received.")
        return self._handle_marketpilot_payload(data, source="command")

    def poll_marketpilot_object_store_signal(self):
        key = str(getattr(self, "marketpilot_object_store_signal_key", "") or "").strip()
        if not key:
            return False
        if key in self.marketpilot_processed_object_store_keys:
            return False

        object_store = getattr(self, "object_store", getattr(self, "ObjectStore", None))
        if object_store is None:
            self.latest_object_store_receipt_evidence = {
                "received": False,
                "key": key,
                "reason": "object_store_unavailable",
            }
            return False

        clearer = getattr(object_store, "clear", getattr(object_store, "Clear", None))
        if callable(clearer):
            clearer()

        contains = getattr(object_store, "contains_key", getattr(object_store, "ContainsKey", None))
        if callable(contains) and not contains(key):
            return False

        reader = getattr(object_store, "read", getattr(object_store, "Read", None))
        if not callable(reader):
            self.latest_object_store_receipt_evidence = {
                "received": False,
                "key": key,
                "reason": "object_store_read_unavailable",
            }
            return False

        raw_payload = reader(key)
        try:
            payload = json.loads(str(raw_payload))
        except (TypeError, ValueError):
            self.latest_object_store_receipt_evidence = {
                "received": True,
                "key": key,
                "reason": "malformed_object_store_json",
            }
            self.marketpilot_processed_object_store_keys.add(key)
            self.debug("MarketPilot Object Store signal rejected: malformed_object_store_json")
            return False

        self.latest_object_store_receipt_evidence = {
            "received": True,
            "key": key,
            "payload_kind": type(payload).__name__,
            "has_command_type": _has_safe_field(payload, "command_type", "CommandType"),
        }
        self.debug("MarketPilot Object Store signal received.")
        accepted = self._handle_marketpilot_payload(payload, source="object_store")
        if accepted is not None:
            self.marketpilot_processed_object_store_keys.add(key)
        return bool(accepted)

    def _handle_marketpilot_payload(self, data, *, source):
        normalized = normalize_marketpilot_command(data)
        if not normalized.accepted:
            self.latest_command_rejection_evidence = {
                "accepted": False,
                "reason": normalized.reason,
                "source": source,
            }
            self.debug(f"MarketPilot command rejected: {normalized.reason}")
            return False

        validation = validate_marketpilot_command(
            normalized.command,
            seen_idempotency_keys=self.marketpilot_seen_command_keys,
            now_utc=self._marketpilot_now_utc(),
        )
        if not validation.accepted:
            self.latest_command_rejection_evidence = {
                "accepted": False,
                "reason": validation.reason,
                "symbol": validation.symbol,
                "source": source,
            }
            self.debug(f"MarketPilot command rejected: {validation.reason}")
            return False

        if not self._marketpilot_symbol_has_tradeable_data(validation.symbol):
            self.latest_command_pending_evidence = {
                "pending": True,
                "reason": "symbol_price_not_ready",
                "symbol": validation.symbol,
                "source": source,
            }
            self.debug(f"MarketPilot command pending: {validation.symbol} price_not_ready")
            if normalized.command.idempotency_key in self.marketpilot_seen_command_keys:
                self.marketpilot_seen_command_keys.remove(normalized.command.idempotency_key)
            return None

        self.market_order(validation.symbol, validation.quantity, tag=validation.tag)
        self.latest_command_pending_evidence = None
        self.latest_command_rejection_evidence = None
        self.debug(f"MarketPilot {source} accepted: {validation.symbol} {validation.quantity}")
        return True

    def on_order_event(self, order_event):
        order_id = _safe_attr(order_event, "order_id", "OrderId")
        tag = self._marketpilot_order_tag(order_id)
        tag_parts = parse_order_tag(tag) if tag else None
        evidence = {
            "order_id": order_id,
            "status": str(_safe_attr(order_event, "status", "Status")),
            "fill_quantity": _safe_attr(order_event, "fill_quantity", "FillQuantity"),
            "fill_price": _safe_attr(order_event, "fill_price", "FillPrice"),
            "tag": tag,
            "signal_id": (tag_parts or {}).get("signal_id"),
            "idempotency_key": (tag_parts or {}).get("idempotency_key"),
        }
        self.latest_order_event_evidence = evidence
        return evidence

    def _marketpilot_now_utc(self):
        value = getattr(self, "time", getattr(self, "Time", None))
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc)
        return datetime.now(timezone.utc)

    def _marketpilot_order_tag(self, order_id):
        transactions = getattr(self, "transactions", getattr(self, "Transactions", None))
        getter = getattr(transactions, "get_order_by_id", None)
        if callable(getter):
            order = getter(order_id)
            return getattr(order, "tag", getattr(order, "Tag", None))
        getter = getattr(transactions, "GetOrderById", None)
        if callable(getter):
            order = getter(order_id)
            return getattr(order, "tag", getattr(order, "Tag", None))
        return None

    def _marketpilot_symbol_has_tradeable_data(self, symbol):
        securities = getattr(self, "securities", getattr(self, "Securities", None))
        security = None
        if securities is not None:
            try:
                security = securities[symbol]
            except Exception:
                getter = getattr(securities, "get", getattr(securities, "Get", None))
                if callable(getter):
                    security = getter(symbol)
        if security is None:
            return True
        has_data = getattr(security, "has_data", getattr(security, "HasData", True))
        price = getattr(security, "price", getattr(security, "Price", 0))
        try:
            return bool(has_data) and float(price or 0) > 0
        except (TypeError, ValueError):
            return False

    def _marketpilot_object_store_signal_key(self):
        configured = str(getattr(self, "MARKETPILOT_OBJECT_STORE_SIGNAL_KEY", "") or "").strip()
        if configured:
            return configured
        getter = getattr(self, "get_parameter", getattr(self, "GetParameter", None))
        if callable(getter):
            value = getter("marketpilot_object_store_signal_key")
            return str(value or "").strip()
        return ""

    def _schedule_marketpilot_object_store_polling(self):
        if not self.marketpilot_object_store_signal_key:
            return False
        schedule = getattr(self, "schedule", getattr(self, "Schedule", None))
        date_rules = getattr(self, "date_rules", getattr(self, "DateRules", None))
        time_rules = getattr(self, "time_rules", getattr(self, "TimeRules", None))
        if schedule is None or date_rules is None or time_rules is None:
            return False
        on_method = getattr(schedule, "on", getattr(schedule, "On", None))
        every_day = getattr(date_rules, "every_day", getattr(date_rules, "EveryDay", None))
        every = getattr(time_rules, "every", getattr(time_rules, "Every", None))
        if not callable(on_method) or not callable(every_day) or not callable(every):
            return False
        on_method(every_day(), every(timedelta(minutes=1)), self.poll_marketpilot_object_store_signal)
        return True


def _safe_attr(obj, *names):
    for name in names:
        if hasattr(obj, name):
            return getattr(obj, name)
    return None


def _has_safe_field(obj, *names):
    if isinstance(obj, dict):
        lowered = {str(key).lower() for key in obj}
        return any(name in obj or name.lower() in lowered for name in names)
    return any(hasattr(obj, name) for name in names)
