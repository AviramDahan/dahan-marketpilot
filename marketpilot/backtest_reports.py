"""Backtest report contracts and artifact classification."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Sequence


DISCLAIMER = "SIMULATED PAPER TRADING ONLY - NOT FINANCIAL ADVICE"


class ArtifactSource(str, Enum):
    REAL_QUANTCONNECT = "real_quantconnect"
    FIXTURE = "fixture"
    SCHEMA = "schema"
    EXAMPLE = "example"
    NOT_RUN = "not_run"


class WindowStatus(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class ValidationWindow:
    name: str
    start_year: int | None
    end_year: int | None
    status: WindowStatus
    reason: str | None = None

    @property
    def available(self) -> bool:
        return self.status is WindowStatus.AVAILABLE


@dataclass(frozen=True)
class BacktestReport:
    title: str
    source: ArtifactSource
    windows: tuple[ValidationWindow, ...]
    assumptions: Mapping[str, object]
    limitations: tuple[str, ...]
    missing_data_warnings: tuple[str, ...]
    benchmark_comparison: Mapping[str, object] = field(default_factory=dict)
    activation_outcome: Mapping[str, object] = field(default_factory=dict)
    metrics: Mapping[str, float] = field(default_factory=dict)
    disclaimer: str = DISCLAIMER

    @property
    def report_complete(self) -> bool:
        required_windows = {"full_period", "in_sample", "out_of_sample"}
        names = {window.name for window in self.windows}
        return (
            self.disclaimer == DISCLAIMER
            and bool(required_windows & names)
            and bool(self.assumptions)
            and bool(self.limitations)
            and bool(self.activation_outcome)
        )


def build_validation_windows(start_year: int, end_year: int, in_sample_end_year: int) -> tuple[ValidationWindow, ...]:
    if end_year < start_year:
        raise ValueError("end_year must be greater than or equal to start_year.")

    windows: list[ValidationWindow] = [
        ValidationWindow("full_period", start_year, end_year, WindowStatus.AVAILABLE),
    ]
    windows.extend(ValidationWindow(f"year_{year}", year, year, WindowStatus.AVAILABLE) for year in range(start_year, end_year + 1))

    if in_sample_end_year < start_year:
        windows.append(ValidationWindow("in_sample", None, None, WindowStatus.UNAVAILABLE, "insufficient_history"))
    else:
        windows.append(ValidationWindow("in_sample", start_year, min(in_sample_end_year, end_year), WindowStatus.AVAILABLE))

    if in_sample_end_year + 1 > end_year:
        windows.append(ValidationWindow("out_of_sample", None, None, WindowStatus.UNAVAILABLE, "insufficient_out_of_sample_history"))
    else:
        windows.append(ValidationWindow("out_of_sample", in_sample_end_year + 1, end_year, WindowStatus.AVAILABLE))

    return tuple(windows)


def build_backtest_report(
    *,
    title: str,
    source: ArtifactSource | str,
    windows: Sequence[ValidationWindow],
    assumptions: Mapping[str, object],
    limitations: Sequence[str],
    missing_data_warnings: Sequence[str] = (),
    benchmark_comparison: Mapping[str, object] | None = None,
    activation_outcome: Mapping[str, object] | None = None,
    metrics: Mapping[str, float] | None = None,
) -> BacktestReport:
    artifact_source = source if isinstance(source, ArtifactSource) else ArtifactSource(str(source))
    safe_metrics = dict(metrics or {})
    if artifact_source is not ArtifactSource.REAL_QUANTCONNECT and safe_metrics:
        raise ValueError("Only documented real QuantConnect artifacts may contain performance metrics.")
    if not limitations:
        raise ValueError("Reports must include limitations.")
    return BacktestReport(
        title=title,
        source=artifact_source,
        windows=tuple(windows),
        assumptions=dict(assumptions),
        limitations=tuple(limitations),
        missing_data_warnings=tuple(missing_data_warnings),
        benchmark_comparison=dict(benchmark_comparison or {}),
        activation_outcome=dict(activation_outcome or {}),
        metrics=safe_metrics,
    )


def report_to_dict(report: BacktestReport) -> dict[str, object]:
    return {
        "title": report.title,
        "source": report.source.value,
        "disclaimer": report.disclaimer,
        "windows": [
            {
                "name": window.name,
                "start_year": window.start_year,
                "end_year": window.end_year,
                "status": window.status.value,
                "reason": window.reason,
            }
            for window in report.windows
        ],
        "assumptions": dict(report.assumptions),
        "limitations": list(report.limitations),
        "missing_data_warnings": list(report.missing_data_warnings),
        "benchmark_comparison": dict(report.benchmark_comparison),
        "activation_outcome": dict(report.activation_outcome),
        "metrics": dict(report.metrics),
    }


def render_backtest_report(report: BacktestReport) -> str:
    lines = [
        f"# {report.title}",
        "",
        report.disclaimer,
        "",
        f"Artifact source: `{report.source.value}`",
        "",
        "## Windows",
    ]
    for window in report.windows:
        period = "unavailable" if not window.available else f"{window.start_year}-{window.end_year}"
        reason = f" ({window.reason})" if window.reason else ""
        lines.append(f"- {window.name}: {window.status.value} {period}{reason}")

    lines.extend(["", "## Assumptions"])
    lines.extend(f"- {key}: {value}" for key, value in report.assumptions.items())
    lines.extend(["", "## Limitations"])
    lines.extend(f"- {item}" for item in report.limitations)

    if report.missing_data_warnings:
        lines.extend(["", "## Missing Data Warnings"])
        lines.extend(f"- {item}" for item in report.missing_data_warnings)

    lines.extend(["", "## Benchmark Comparison", str(dict(report.benchmark_comparison))])
    lines.extend(["", "## Activation Outcome", str(dict(report.activation_outcome))])
    return "\n".join(lines).strip() + "\n"
