"""The JSON shapes of the forecasts endpoints."""

import datetime

from pydantic import BaseModel


class ForecastOut(BaseModel):
    """One day of forecast for one city."""

    city: str
    date: datetime.date
    temp_max_c: float | None
    temp_min_c: float | None
    precipitation_mm: float | None


class ForecastList(BaseModel):
    """The answer of GET /v1/forecasts: one page of items and the paging numbers."""

    items: list[ForecastOut]
    limit: int
    offset: int
    total: int
