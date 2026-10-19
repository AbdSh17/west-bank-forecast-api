"""The report endpoints."""

from datetime import date

from fastapi import APIRouter, Depends

from api_to_sqlite.cities.dao import CityDAO
from api_to_sqlite.database import Connection, get_connection
from api_to_sqlite.reports import service
from api_to_sqlite.reports.dao import ReportDAO
from api_to_sqlite.reports.schemas import (
    AverageMaxReport,
    HottestDayReport,
    RainyDaysReport,
)

router = APIRouter(prefix="/v1/reports", tags=["reports"])


@router.get("/average-max")
def average_max(
    city: str | None = None,
    start_date: date | None = None,
    conn: Connection = Depends(get_connection),
    cities: CityDAO = Depends(CityDAO),
    reports: ReportDAO = Depends(ReportDAO),
) -> AverageMaxReport:
    """Average maximum temperature per city, hottest first."""
    return service.average_max(conn, cities, reports, start_date or date.today(), city)


@router.get("/hottest-day")
def hottest_day(
    city: str | None = None,
    start_date: date | None = None,
    conn: Connection = Depends(get_connection),
    cities: CityDAO = Depends(CityDAO),
    reports: ReportDAO = Depends(ReportDAO),
) -> HottestDayReport:
    """The hottest day of each city. A tie shows every tied day."""
    return service.hottest_day(conn, cities, reports, start_date or date.today(), city)


@router.get("/rainy-days")
def rainy_days(
    city: str | None = None,
    start_date: date | None = None,
    conn: Connection = Depends(get_connection),
    cities: CityDAO = Depends(CityDAO),
    reports: ReportDAO = Depends(ReportDAO),
) -> RainyDaysReport:
    """Days with precipitation above 0 per city. A city with no data shows 0."""
    return service.rainy_days(conn, cities, reports, start_date or date.today(), city)
