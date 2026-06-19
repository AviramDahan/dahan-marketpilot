from __future__ import annotations

"""Deterministic universe source loading for simulation-only scanner runs."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping

import yaml

from marketpilot.data_quality import UniverseCandidate, UniverseDecision, UniverseSnapshot
from marketpilot.universe import build_universe_snapshot, load_universe_config


DEFAULT_SIMULATION_UNIVERSE_CONFIG = Path(__file__).resolve().parents[1] / "config" / "simulation_universe.yaml"


@dataclass(frozen=True)
class UniverseSourceRow:
    symbol: str
    source: str = "static"
    price: float | int | None = None
    history_bars: int | None = None
    average_volume_20: float | int | None = None
    average_dollar_volume_20: float | int | None = None
    market_cap: float | int | None = None
    sector: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    @property
    def normalized_symbol(self) -> str:
        return self.symbol.strip().upper()


@dataclass(frozen=True)
class UniverseSourceSnapshot:
    universe: UniverseSnapshot
    source_rows: tuple[UniverseSourceRow, ...]
    duplicate_symbols: tuple[str, ...] = ()
    product_mode: str = "simulation_only"

    @property
    def accepted_symbols(self) -> tuple[str, ...]:
        return self.universe.accepted_symbols

    @property
    def rejected_symbols(self) -> tuple[str, ...]:
        return self.universe.rejected_symbols


def load_simulation_universe_config(path: str | Path = DEFAULT_SIMULATION_UNIVERSE_CONFIG) -> dict[str, object]:
    with Path(path).open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    config = loaded.get("simulation_universe", loaded)
    if not isinstance(config, dict):
        raise ValueError("simulation universe config must be a mapping.")
    if config.get("product_mode") != "simulation_only":
        raise ValueError("simulation universe requires product_mode: simulation_only.")
    if config.get("paper_trading_only") is not True:
        raise ValueError("simulation universe requires paper_trading_only: true.")
    return config


def load_universe_source_rows(path: str | Path = DEFAULT_SIMULATION_UNIVERSE_CONFIG) -> tuple[UniverseSourceRow, ...]:
    config = load_simulation_universe_config(path)
    rows = config.get("symbols", ())
    if not isinstance(rows, list):
        raise ValueError("simulation universe symbols must be a list.")
    parsed = tuple(_row_from_mapping(row, index=index) for index, row in enumerate(rows))
    return dedupe_universe_rows(parsed)[0]


def dedupe_universe_rows(rows: Iterable[UniverseSourceRow]) -> tuple[tuple[UniverseSourceRow, ...], tuple[str, ...]]:
    seen: set[str] = set()
    deduped: list[UniverseSourceRow] = []
    duplicates: list[str] = []
    for row in rows:
        symbol = row.normalized_symbol
        if not symbol:
            deduped.append(row)
            continue
        if symbol in seen:
            duplicates.append(symbol)
            continue
        seen.add(symbol)
        deduped.append(row)
    return tuple(deduped), tuple(duplicates)


def build_simulation_universe_snapshot(
    rows: Iterable[UniverseSourceRow],
    *,
    universe_config: Mapping[str, object] | None = None,
    previous_accepted: Iterable[str] = (),
) -> UniverseSourceSnapshot:
    deduped, duplicates = dedupe_universe_rows(rows)
    config = dict(universe_config or load_universe_config())
    candidates = tuple(_candidate_from_row(row) for row in deduped)
    snapshot = build_universe_snapshot(candidates, config, previous_accepted=previous_accepted)
    return UniverseSourceSnapshot(universe=snapshot, source_rows=deduped, duplicate_symbols=duplicates)


def decision_reason_map(snapshot: UniverseSourceSnapshot) -> dict[str, tuple[str, ...]]:
    return {
        decision.symbol: tuple(issue.value for issue in decision.issues)
        for decision in snapshot.universe.decisions
    }


def _row_from_mapping(row: object, *, index: int) -> UniverseSourceRow:
    if not isinstance(row, Mapping):
        raise ValueError(f"simulation universe row {index} must be a mapping.")
    symbol = str(row.get("symbol") or "").strip().upper()
    source = str(row.get("source") or "static").strip() or "static"
    return UniverseSourceRow(
        symbol=symbol,
        source=source,
        price=_optional_number(row.get("price")),
        history_bars=_optional_int(row.get("history_bars")),
        average_volume_20=_optional_number(row.get("average_volume_20")),
        average_dollar_volume_20=_optional_number(row.get("average_dollar_volume_20")),
        market_cap=_optional_number(row.get("market_cap")),
        sector=str(row.get("sector") or "").strip() or None,
        metadata={key: value for key, value in row.items() if key not in _known_row_fields()},
    )


def _candidate_from_row(row: UniverseSourceRow) -> UniverseCandidate:
    missing = []
    for field_name in ("price", "history_bars", "average_volume_20", "average_dollar_volume_20"):
        if getattr(row, field_name) is None:
            missing.append(field_name)
    return UniverseCandidate(
        symbol=row.normalized_symbol,
        price=row.price,
        history_bars=row.history_bars,
        average_volume_20=row.average_volume_20,
        average_dollar_volume_20=row.average_dollar_volume_20,
        market_cap=row.market_cap,
        sector=row.sector,
        missing_fields=tuple(missing),
    )


def _optional_number(value: object) -> float | int | None:
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        raise ValueError("numeric universe fields must not be boolean.")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"universe numeric field is malformed: {value}") from exc


def _optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(str(value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"universe integer field is malformed: {value}") from exc


def _known_row_fields() -> set[str]:
    return {
        "symbol",
        "source",
        "price",
        "history_bars",
        "average_volume_20",
        "average_dollar_volume_20",
        "market_cap",
        "sector",
    }


__all__ = [
    "UniverseSourceRow",
    "UniverseSourceSnapshot",
    "build_simulation_universe_snapshot",
    "decision_reason_map",
    "dedupe_universe_rows",
    "load_simulation_universe_config",
    "load_universe_source_rows",
]

