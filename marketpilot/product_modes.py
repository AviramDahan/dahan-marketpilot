from __future__ import annotations

"""Product mode contracts for the scanner simulator pivot."""

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from marketpilot.constants import PAPER_TRADING_ONLY


class ProductMode(str, Enum):
    SIMULATION_ONLY = "simulation_only"
    QC_PAPER_VALIDATION = "qc_paper_validation"
    QC_NATIVE_ALGORITHM = "qc_native_algorithm"


@dataclass(frozen=True)
class ProductModeCapabilities:
    mode: ProductMode
    implemented_now: bool
    requires_quantconnect: bool
    allows_broker_credentials: bool
    allows_real_orders: bool
    dashboard_mutation_allowed: bool
    submits_quantconnect_orders: bool
    description: str


_CAPABILITIES: dict[ProductMode, ProductModeCapabilities] = {
    ProductMode.SIMULATION_ONLY: ProductModeCapabilities(
        mode=ProductMode.SIMULATION_ONLY,
        implemented_now=True,
        requires_quantconnect=False,
        allows_broker_credentials=False,
        allows_real_orders=False,
        dashboard_mutation_allowed=False,
        submits_quantconnect_orders=False,
        description="Core MVP mode: scanner plus internal paper simulator.",
    ),
    ProductMode.QC_PAPER_VALIDATION: ProductModeCapabilities(
        mode=ProductMode.QC_PAPER_VALIDATION,
        implemented_now=False,
        requires_quantconnect=True,
        allows_broker_credentials=False,
        allows_real_orders=False,
        dashboard_mutation_allowed=False,
        submits_quantconnect_orders=True,
        description="Parked optional mode for external QuantConnect Paper validation.",
    ),
    ProductMode.QC_NATIVE_ALGORITHM: ProductModeCapabilities(
        mode=ProductMode.QC_NATIVE_ALGORITHM,
        implemented_now=False,
        requires_quantconnect=True,
        allows_broker_credentials=False,
        allows_real_orders=False,
        dashboard_mutation_allowed=False,
        submits_quantconnect_orders=True,
        description="Future-only mode where QC/LEAN owns selection and execution.",
    ),
}


def parse_product_mode(value: object | None) -> ProductMode:
    if isinstance(value, ProductMode):
        return value
    normalized = str(value or ProductMode.SIMULATION_ONLY.value).strip().lower()
    for mode in ProductMode:
        if normalized == mode.value:
            return mode
    raise ValueError(f"unsupported product mode: {value}")


def product_mode_capabilities(mode: ProductMode | str | None = None) -> ProductModeCapabilities:
    return _CAPABILITIES[parse_product_mode(mode)]


def assert_simulation_only_safety(
    *,
    mode: ProductMode | str | None = None,
    env: Mapping[str, str] | None = None,
) -> ProductModeCapabilities:
    capabilities = product_mode_capabilities(mode)
    if PAPER_TRADING_ONLY is not True:
        raise RuntimeError("PAPER_TRADING_ONLY must remain True.")
    if capabilities.mode is not ProductMode.SIMULATION_ONLY:
        raise RuntimeError("Phase 16.3 implements only simulation_only mode.")
    if capabilities.requires_quantconnect:
        raise RuntimeError("simulation_only must not require QuantConnect.")
    if capabilities.allows_broker_credentials or capabilities.allows_real_orders:
        raise RuntimeError("simulation_only must not allow broker credentials or real orders.")
    source = env or {}
    forbidden_present = tuple(name for name in _forbidden_live_keys() if str(source.get(name) or "").strip())
    if forbidden_present:
        raise RuntimeError(f"simulation_only rejects live trading configuration: {', '.join(forbidden_present)}")
    return capabilities


def product_mode_summary(mode: ProductMode | str | None = None) -> dict[str, object]:
    capabilities = product_mode_capabilities(mode)
    return {
        "mode": capabilities.mode.value,
        "implemented_now": capabilities.implemented_now,
        "requires_quantconnect": capabilities.requires_quantconnect,
        "allows_broker_credentials": capabilities.allows_broker_credentials,
        "allows_real_orders": capabilities.allows_real_orders,
        "dashboard_mutation_allowed": capabilities.dashboard_mutation_allowed,
        "submits_quantconnect_orders": capabilities.submits_quantconnect_orders,
        "paper_trading_only": PAPER_TRADING_ONLY is True,
        "description": capabilities.description,
    }


def _forbidden_live_keys() -> tuple[str, ...]:
    return (
        "BROKER_API_KEY",
        "BROKER_API_SECRET",
        "LIVE_BROKERAGE_USERNAME",
        "LIVE_BROKERAGE_PASSWORD",
        "REAL_MONEY_ENABLED",
        "ALLOW_REAL_ORDERS",
    )


__all__ = [
    "ProductMode",
    "ProductModeCapabilities",
    "assert_simulation_only_safety",
    "parse_product_mode",
    "product_mode_capabilities",
    "product_mode_summary",
]
