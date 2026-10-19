"""Plain objects of the forecasts package. No HTTP and no SQL here."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ForecastFilter:
    """Which forecast rows to read: from a date, optionally to a date, one city."""

    start_date: str
    end_date: str | None = None
    city: str | None = None


@dataclass(frozen=True)
class Page:
    """One page of a list: how many rows to return and how many to skip."""

    limit: int = 50
    offset: int = 0
