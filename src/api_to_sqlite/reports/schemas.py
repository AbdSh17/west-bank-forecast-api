"""The JSON shapes of the report endpoints."""

import datetime

from pydantic import BaseModel


class AverageMaxOut(BaseModel):
    """The average maximum temperature of one city."""

    city: str
    avg_max_c: float | None


class AverageMaxReport(BaseModel):
    """The answer of GET /v1/reports/average-max, hottest city first."""

    start_date: datetime.date
    items: list[AverageMaxOut]


class HottestDayOut(BaseModel):
    """The hottest day of one city. A tie shows every tied day."""

    city: str
    date: datetime.date
    temp_max_c: float


class HottestDayReport(BaseModel):
    """The answer of GET /v1/reports/hottest-day."""

    start_date: datetime.date
    items: list[HottestDayOut]


class RainyDaysOut(BaseModel):
    """The number of days with precipitation above 0 for one city."""

    city: str
    rainy_days: int


class RainyDaysReport(BaseModel):
    """The answer of GET /v1/reports/rainy-days."""

    start_date: datetime.date
    items: list[RainyDaysOut]
