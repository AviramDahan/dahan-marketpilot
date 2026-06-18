import json
from datetime import datetime, timedelta, timezone

from AlgorithmImports import QCAlgorithm, Resolution


class DahanMarketPilotRuntime(QCAlgorithm):
    """Self-contained QuantConnect Paper adapter for MarketPilot commands."""

    MARKETPILOT_OBJECT_STORE_SIGNAL_KEY = ""
    DEFAULT_MARKETPILOT_OBJECT_STORE_SIGNAL_KEY = ""

    def initialize(self):
        self.set_start_date(2026, 1, 1)
        self.set_cash(27027.03)

        self.marketpilot_seen_idempotency_keys = set()
        self.marketpilot_seen_command_keys = self.marketpilot_seen_idempotency_keys
        self.marketpilot_object_store_signal_key = self._marketpilot_object_store_signal_key()
        self.marketpilot_processed_object_store_keys = set()
        self.latest_command_receipt_evidence = None
        self.latest_object_store_receipt_evidence = None
        self.latest_command_rejection_evidence = None
        self.latest_command_pending_evidence = None
        self.latest_order_event_evidence = None
        self.marketpilot_last_object_store_poll_at = None

        minute = getattr(Resolution, "MINUTE", getattr(Resolution, "Minute", Resolution.DAILY))
        self.add_equity("SPY", minute)
        self.add_equity("QQQ", minute)
        self._schedule_marketpilot_object_store_polling()

        self.debug("SIMULATED PAPER TRADING ONLY - NOT FINANCIAL ADVICE")

    def on_command(self, data):
        self.latest_command_receipt_evidence = {
            "received": True,
            "payload_kind": type(data).__name__,
            "has_command_type": self._payload_get(self._payload_dict(data), "command_type") is not None,
            "has_type": "$type" in self._payload_dict(data) or "type" in self._payload_dict(data),
        }
        self.debug("MarketPilot command received.")
        return self._handle_marketpilot_payload(data, source="command")

    def on_data(self, data):
        if not self.marketpilot_object_store_signal_key:
            return
        now = self._marketpilot_now_utc()
        last_poll = self.marketpilot_last_object_store_poll_at
        if last_poll is not None and (now - last_poll).total_seconds() < 20:
            return
        self.marketpilot_last_object_store_poll_at = now
        self.poll_marketpilot_object_store_signal()

    def poll_marketpilot_object_store_signal(self):
        key = str(getattr(self, "marketpilot_object_store_signal_key", "") or "").strip()
        if not key or key in self.marketpilot_processed_object_store_keys:
            return False

        object_store = getattr(self, "object_store", getattr(self, "ObjectStore", None))
        if object_store is None:
            self.latest_object_store_receipt_evidence = {
                "received": False,
                "key": key,
                "reason": "object_store_unavailable",
            }
            self.debug("MarketPilot Object Store signal rejected: object_store_unavailable")
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
            self.debug("MarketPilot Object Store signal rejected: object_store_read_unavailable")
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
            "has_command_type": self._payload_get(payload, "command_type") is not None,
        }
        self.debug("MarketPilot Object Store signal received.")
        accepted = self._handle_marketpilot_payload(payload, source="object_store")
        if accepted is not None:
            self.marketpilot_processed_object_store_keys.add(key)
        return bool(accepted)

    def _handle_marketpilot_payload(self, data, *, source):
        payload = self._payload_dict(data)
        command_type = str(self._payload_get(payload, "command_type") or "").strip()
        if command_type != "marketpilot_signal":
            self.latest_command_rejection_evidence = {
                "accepted": False,
                "reason": "unsupported_command_type",
                "source": source,
            }
            self.debug(
                "MarketPilot command rejected: unsupported_command_type "
                f"payload_keys={self._safe_payload_keys(payload)} "
                f"envelope_types={self._safe_envelope_types(payload)}"
            )
            return False

        if self._payload_get(payload, "paper_trading_only") is not True:
            self.latest_command_rejection_evidence = {
                "accepted": False,
                "reason": "paper_trading_only_required",
                "source": source,
            }
            self.debug("MarketPilot command rejected: paper_trading_only_required")
            return False

        correlation_id = self._required_text(payload, "correlation_id")
        signal_id = self._required_text(payload, "signal_id")
        idempotency_key = self._required_text(payload, "idempotency_key")
        symbol = self._required_text(payload, "symbol").upper()
        quantity = self._required_int(payload, "quantity")
        expires_at = self._parse_utc(self._payload_get(payload, "expires_at_utc"))
        signal_time = self._parse_utc(self._payload_get(payload, "signal_time_utc"))

        if not correlation_id or not signal_id or not idempotency_key or not symbol:
            self.latest_command_rejection_evidence = {
                "accepted": False,
                "reason": "missing_required_field",
                "source": source,
            }
            self.debug("MarketPilot command rejected: missing_required_field")
            return False
        if quantity <= 0:
            self.latest_command_rejection_evidence = {
                "accepted": False,
                "reason": "invalid_quantity",
                "symbol": symbol,
                "source": source,
            }
            self.debug("MarketPilot command rejected: invalid_quantity")
            return False
        if signal_time is None:
            self.latest_command_rejection_evidence = {
                "accepted": False,
                "reason": "invalid_signal_time",
                "symbol": symbol,
                "source": source,
            }
            self.debug("MarketPilot command rejected: invalid_signal_time")
            return False
        if expires_at is None or expires_at < self._marketpilot_now_utc():
            self.latest_command_rejection_evidence = {
                "accepted": False,
                "reason": "expired_signal",
                "symbol": symbol,
                "source": source,
            }
            self.debug("MarketPilot command rejected: expired_signal")
            return False
        if idempotency_key in self.marketpilot_seen_idempotency_keys:
            self.latest_command_rejection_evidence = {
                "accepted": False,
                "reason": "duplicate_idempotency_key",
                "symbol": symbol,
                "source": source,
            }
            self.debug("MarketPilot command rejected: duplicate_idempotency_key")
            return False
        if not self._marketpilot_symbol_has_tradeable_data(symbol):
            self.latest_command_pending_evidence = {
                "pending": True,
                "reason": "symbol_price_not_ready",
                "symbol": symbol,
                "source": source,
            }
            self.debug(f"MarketPilot command pending: {symbol} price_not_ready")
            return None

        tag = f"mp:{signal_id}:{idempotency_key}"
        self.marketpilot_seen_idempotency_keys.add(idempotency_key)
        self.market_order(symbol, quantity, tag=tag)
        self.latest_command_pending_evidence = None
        self.latest_command_rejection_evidence = None
        self.debug(f"MarketPilot {source} accepted: {symbol} {quantity}")
        return True

    def on_order_event(self, order_event):
        order_id = self._safe_attr(order_event, "order_id", "OrderId")
        tag = self._marketpilot_order_tag(order_id)
        parts = str(tag or "").split(":")
        evidence = {
            "order_id": order_id,
            "status": str(self._safe_attr(order_event, "status", "Status")),
            "fill_quantity": self._safe_attr(order_event, "fill_quantity", "FillQuantity"),
            "fill_price": self._safe_attr(order_event, "fill_price", "FillPrice"),
            "tag": tag,
            "signal_id": parts[1] if len(parts) == 3 and parts[0] == "mp" else None,
            "idempotency_key": parts[2] if len(parts) == 3 and parts[0] == "mp" else None,
        }
        self.latest_order_event_evidence = evidence
        return evidence

    def _marketpilot_object_store_signal_key(self):
        configured = str(getattr(self, "MARKETPILOT_OBJECT_STORE_SIGNAL_KEY", "") or "").strip()
        if configured:
            return configured
        getter = getattr(self, "get_parameter", getattr(self, "GetParameter", None))
        if callable(getter):
            value = getter("marketpilot_object_store_signal_key")
            if str(value or "").strip():
                return str(value or "").strip()
        return str(getattr(self, "DEFAULT_MARKETPILOT_OBJECT_STORE_SIGNAL_KEY", "") or "").strip()

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
        if callable(on_method) and callable(every_day) and callable(every):
            on_method(every_day(), every(timedelta(minutes=1)), self.poll_marketpilot_object_store_signal)
            return True
        return False

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

    def _marketpilot_order_tag(self, order_id):
        transactions = getattr(self, "transactions", getattr(self, "Transactions", None))
        for name in ("get_order_by_id", "GetOrderById"):
            getter = getattr(transactions, name, None)
            if callable(getter):
                order = getter(order_id)
                return getattr(order, "tag", getattr(order, "Tag", None))
        return None

    def _payload_dict(self, data):
        if isinstance(data, dict):
            return self._unwrap_payload_envelope(data)
        if isinstance(data, str):
            try:
                loaded = json.loads(data)
                return self._unwrap_payload_envelope(loaded) if isinstance(loaded, dict) else {}
            except (TypeError, ValueError):
                return {}
        dynamic_payload = self._dynamic_payload_dict(data)
        if dynamic_payload:
            return dynamic_payload
        return self._unwrap_payload_envelope({
            name: getattr(data, name)
            for name in dir(data)
            if not name.startswith("_") and not callable(getattr(data, name))
        })

    def _dynamic_payload_dict(self, data):
        keys = (
            "command_type",
            "correlation_id",
            "signal_id",
            "idempotency_key",
            "symbol",
            "quantity",
            "signal_time_utc",
            "expires_at_utc",
            "paper_trading_only",
        )
        values = {}
        for key in keys:
            for candidate in (key, key[:1].upper() + key[1:]):
                try:
                    value = data[candidate]
                except Exception:
                    continue
                values[key] = value
                break
        return values

    def _unwrap_payload_envelope(self, payload):
        if not isinstance(payload, dict):
            return {}
        for key in ("payload_data", "PayloadData", "payloadData"):
            value = payload.get(key)
            if isinstance(value, dict):
                return self._unwrap_payload_envelope(value)
            if isinstance(value, str):
                try:
                    decoded = json.loads(value)
                except (TypeError, ValueError):
                    return payload
                if isinstance(decoded, dict):
                    return self._unwrap_payload_envelope(decoded)
            if value is not None:
                decoded = self._payload_value_to_dict(value)
                if decoded:
                    return self._unwrap_payload_envelope(decoded)
        return payload

    def _payload_value_to_dict(self, value):
        items = getattr(value, "items", None)
        if callable(items):
            try:
                return {str(key): item_value for key, item_value in items()}
            except Exception:
                pass
        keys = getattr(value, "Keys", getattr(value, "keys", None))
        if keys is not None:
            try:
                return {str(key): value[key] for key in keys}
            except Exception:
                pass
        try:
            decoded = json.loads(str(value))
        except (TypeError, ValueError):
            decoded = None
        if isinstance(decoded, dict):
            return decoded
        to_string = getattr(value, "ToString", None)
        if callable(to_string):
            try:
                decoded = json.loads(str(to_string()))
            except (TypeError, ValueError):
                decoded = None
            if isinstance(decoded, dict):
                return decoded
        if isinstance(value, (bool, int, float, bytes, bytearray)):
            return {}
        try:
            return {
                name: getattr(value, name)
                for name in dir(value)
                if not name.startswith("_") and not callable(getattr(value, name))
            }
        except Exception:
            return {}

    def _safe_payload_keys(self, payload):
        if not isinstance(payload, dict):
            return []
        return sorted(str(key) for key in payload.keys())[:30]

    def _safe_envelope_types(self, payload):
        if not isinstance(payload, dict):
            return []
        values = []
        for key in ("payload_data", "PayloadData", "payloadData"):
            if key not in payload:
                continue
            value = payload.get(key)
            preview = ""
            try:
                preview = str(value)[:80]
            except Exception:
                preview = "<unprintable>"
            values.append(f"{key}:{type(value).__name__}:{preview}")
        return values[:5]

    def _required_text(self, payload, key):
        return str(self._payload_get(payload, key) or "").strip()

    def _required_int(self, payload, key):
        try:
            return int(self._payload_get(payload, key) or 0)
        except (TypeError, ValueError):
            return 0

    def _payload_get(self, payload, key):
        if not isinstance(payload, dict):
            return None
        wanted = _key_alias(key)
        for candidate, value in payload.items():
            if _key_alias(candidate) == wanted:
                return value
        return None

    def _parse_utc(self, value):
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return None
        return parsed.astimezone(timezone.utc)

    def _marketpilot_now_utc(self):
        value = getattr(self, "time", getattr(self, "Time", None))
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc)
        return datetime.now(timezone.utc)

    def _safe_attr(self, value, snake_name, pascal_name):
        return getattr(value, snake_name, getattr(value, pascal_name, None))


def _pascal(value):
    return "".join(part.capitalize() for part in str(value).split("_"))


def _key_alias(value):
    return str(value).replace("_", "").lower()
