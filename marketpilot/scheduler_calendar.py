from __future__ import annotations

"""NYSE/ET market-session guard for autonomous paper scheduling."""


from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from enum import Enum
from zoneinfo import ZoneInfo


MARKET_TIMEZONE = "America/New_York"
REGULAR_OPEN_ET = time(9, 30)
REGULAR_CLOSE_ET = time(16, 0)
EARLY_CLOSE_ET = time(13, 0)


class MarketSessionStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    STALE = "stale"


class MarketSkipReason(str, Enum):
    WEEKEND = "weekend"
    HOLIDAY = "holiday"
    BEFORE_OPEN = "before_open"
    AFTER_CLOSE = "after_close"
    STALE_SCHEDULED_CYCLE = "stale_scheduled_cycle"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class MarketSessionDecision:
    eligible_for_orders: bool
    status: MarketSessionStatus
    observed_at_utc: datetime
    observed_at_et: datetime
    market_date: date
    session_open_et: datetime | None
    session_close_et: datetime | None
    reason: MarketSkipReason | None = None
    holiday_name: str | None = None
    early_close: bool = False
    scheduled_for_utc: datetime | None = None
    age_seconds: int | None = None

    def to_json_dict(self) -> dict[str, object]:
        return {
            "eligible_for_orders": self.eligible_for_orders,
            "status": self.status.value,
            "observed_at_utc": self.observed_at_utc.isoformat(),
            "observed_at_et": self.observed_at_et.isoformat(),
            "market_date": self.market_date.isoformat(),
            "session_open_et": self.session_open_et.isoformat() if self.session_open_et else None,
            "session_close_et": self.session_close_et.isoformat() if self.session_close_et else None,
            "reason": self.reason.value if self.reason else None,
            "holiday_name": self.holiday_name,
            "early_close": self.early_close,
            "scheduled_for_utc": self.scheduled_for_utc.isoformat() if self.scheduled_for_utc else None,
            "age_seconds": self.age_seconds,
            "timezone": MARKET_TIMEZONE,
        }


def evaluate_market_session(
    *,
    now: datetime | None = None,
    scheduled_for: datetime | None = None,
    stale_after_seconds: int = 600,
) -> MarketSessionDecision:
    """Return whether a scheduled cycle may create paper-order intent.

    APScheduler handles wakeups, but this guard is the trading eligibility
    authority so DST, market holidays, and stale catch-up cycles are testable
    without a running scheduler.
    """

    observed_utc = _aware_utc(now or datetime.now(timezone.utc), "now")
    scheduled_utc = _aware_utc(scheduled_for, "scheduled_for") if scheduled_for else None
    observed_et = observed_utc.astimezone(ZoneInfo(MARKET_TIMEZONE))
    market_date = observed_et.date()

    if scheduled_utc is not None:
        age_seconds = max(0, int((observed_utc - scheduled_utc).total_seconds()))
        if age_seconds > stale_after_seconds:
            return MarketSessionDecision(
                eligible_for_orders=False,
                status=MarketSessionStatus.STALE,
                observed_at_utc=observed_utc,
                observed_at_et=observed_et,
                market_date=market_date,
                session_open_et=None,
                session_close_et=None,
                reason=MarketSkipReason.STALE_SCHEDULED_CYCLE,
                scheduled_for_utc=scheduled_utc,
                age_seconds=age_seconds,
            )
    else:
        age_seconds = None

    if observed_et.weekday() >= 5:
        return _closed_decision(
            observed_utc=observed_utc,
            observed_et=observed_et,
            reason=MarketSkipReason.WEEKEND,
            scheduled_for_utc=scheduled_utc,
            age_seconds=age_seconds,
        )

    holiday_name = nyse_holiday_name(market_date)
    if holiday_name is not None:
        return _closed_decision(
            observed_utc=observed_utc,
            observed_et=observed_et,
            reason=MarketSkipReason.HOLIDAY,
            holiday_name=holiday_name,
            scheduled_for_utc=scheduled_utc,
            age_seconds=age_seconds,
        )

    session_open, session_close, early_close = market_session_window(market_date)
    if observed_et < session_open:
        return _closed_decision(
            observed_utc=observed_utc,
            observed_et=observed_et,
            reason=MarketSkipReason.BEFORE_OPEN,
            session_open_et=session_open,
            session_close_et=session_close,
            early_close=early_close,
            scheduled_for_utc=scheduled_utc,
            age_seconds=age_seconds,
        )
    if observed_et >= session_close:
        return _closed_decision(
            observed_utc=observed_utc,
            observed_et=observed_et,
            reason=MarketSkipReason.AFTER_CLOSE,
            session_open_et=session_open,
            session_close_et=session_close,
            early_close=early_close,
            scheduled_for_utc=scheduled_utc,
            age_seconds=age_seconds,
        )

    return MarketSessionDecision(
        eligible_for_orders=True,
        status=MarketSessionStatus.OPEN,
        observed_at_utc=observed_utc,
        observed_at_et=observed_et,
        market_date=market_date,
        session_open_et=session_open,
        session_close_et=session_close,
        early_close=early_close,
        scheduled_for_utc=scheduled_utc,
        age_seconds=age_seconds,
    )


def market_session_window(market_date: date) -> tuple[datetime, datetime, bool]:
    tz = ZoneInfo(MARKET_TIMEZONE)
    close_time = EARLY_CLOSE_ET if is_nyse_early_close(market_date) else REGULAR_CLOSE_ET
    return (
        datetime.combine(market_date, REGULAR_OPEN_ET, tzinfo=tz),
        datetime.combine(market_date, close_time, tzinfo=tz),
        close_time == EARLY_CLOSE_ET,
    )


def nyse_holiday_name(day: date) -> str | None:
    holidays = _nyse_holidays(day.year)
    return holidays.get(day)


def is_nyse_early_close(day: date) -> bool:
    if day.weekday() >= 5 or nyse_holiday_name(day) is not None:
        return False
    thanksgiving = _nth_weekday(day.year, 11, 3, 4)
    if day == thanksgiving + timedelta(days=1):
        return True
    if day.month == 12 and day.day == 24:
        return True
    if day.month == 7 and day.day == 3 and date(day.year, 7, 4).weekday() < 5:
        return True
    return False


def _closed_decision(
    *,
    observed_utc: datetime,
    observed_et: datetime,
    reason: MarketSkipReason,
    session_open_et: datetime | None = None,
    session_close_et: datetime | None = None,
    holiday_name: str | None = None,
    early_close: bool = False,
    scheduled_for_utc: datetime | None = None,
    age_seconds: int | None = None,
) -> MarketSessionDecision:
    return MarketSessionDecision(
        eligible_for_orders=False,
        status=MarketSessionStatus.CLOSED,
        observed_at_utc=observed_utc,
        observed_at_et=observed_et,
        market_date=observed_et.date(),
        session_open_et=session_open_et,
        session_close_et=session_close_et,
        reason=reason,
        holiday_name=holiday_name,
        early_close=early_close,
        scheduled_for_utc=scheduled_for_utc,
        age_seconds=age_seconds,
    )


def _aware_utc(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _nyse_holidays(year: int) -> dict[date, str]:
    holidays: dict[date, str] = {
        _observed_fixed(year, 1, 1): "new_years_day",
        _nth_weekday(year, 1, 0, 3): "martin_luther_king_jr_day",
        _nth_weekday(year, 2, 0, 3): "washingtons_birthday",
        _good_friday(year): "good_friday",
        _last_weekday(year, 5, 0): "memorial_day",
        _observed_fixed(year, 6, 19): "juneteenth",
        _observed_fixed(year, 7, 4): "independence_day",
        _nth_weekday(year, 9, 0, 1): "labor_day",
        _nth_weekday(year, 11, 3, 4): "thanksgiving_day",
        _observed_fixed(year, 12, 25): "christmas_day",
    }
    return holidays


def _observed_fixed(year: int, month: int, day: int) -> date:
    actual = date(year, month, day)
    if actual.weekday() == 5:
        return actual - timedelta(days=1)
    if actual.weekday() == 6:
        return actual + timedelta(days=1)
    return actual


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    current = date(year, month, 1)
    while current.weekday() != weekday:
        current += timedelta(days=1)
    return current + timedelta(days=7 * (n - 1))


def _last_weekday(year: int, month: int, weekday: int) -> date:
    if month == 12:
        current = date(year, 12, 31)
    else:
        current = date(year, month + 1, 1) - timedelta(days=1)
    while current.weekday() != weekday:
        current -= timedelta(days=1)
    return current


def _good_friday(year: int) -> date:
    # Anonymous Gregorian computus; NYSE observes Good Friday.
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    easter = date(year, month, day)
    return easter - timedelta(days=2)


__all__ = [
    "EARLY_CLOSE_ET",
    "MARKET_TIMEZONE",
    "REGULAR_CLOSE_ET",
    "REGULAR_OPEN_ET",
    "MarketSessionDecision",
    "MarketSessionStatus",
    "MarketSkipReason",
    "evaluate_market_session",
    "is_nyse_early_close",
    "market_session_window",
    "nyse_holiday_name",
]

