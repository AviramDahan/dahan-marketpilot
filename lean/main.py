from datetime import datetime, timezone

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

    def initialize(self):
        self.set_start_date(2026, 1, 1)
        self.set_end_date(2026, 1, 31)
        self.set_cash(27027.03)

        self.runtime_bridge: LeanRuntimeBridge = initialize_runtime_bridge()
        self.latest_runtime_result = None
        self.latest_dashboard_export_evidence = self.runtime_bridge.export_dashboard_evidence(None)
        self.marketpilot_seen_command_keys = set()
        self.latest_order_event_evidence = None
        self.latest_command_rejection_evidence = None

        self.add_equity("SPY", Resolution.DAILY)
        self.add_equity("QQQ", Resolution.DAILY)
        self.add_universe(self.select_dynamic_universe)

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
        normalized = normalize_marketpilot_command(data)
        if not normalized.accepted:
            self.latest_command_rejection_evidence = {
                "accepted": False,
                "reason": normalized.reason,
            }
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
            }
            return False

        self.market_order(validation.symbol, validation.quantity, tag=validation.tag)
        self.latest_command_rejection_evidence = None
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


def _safe_attr(obj, *names):
    for name in names:
        if hasattr(obj, name):
            return getattr(obj, name)
    return None
