"""The rules for the reports. No HTTP and no SQL here."""

from datetime import date

from api_to_sqlite.cities.dao import CityDAO
from api_to_sqlite.cities.exceptions import CityNotFound
from api_to_sqlite.database import Connection
from api_to_sqlite.reports.dao import ReportDAO
from api_to_sqlite.reports.schemas import (
    AverageMaxOut,
    AverageMaxReport,
    HottestDayOut,
    HottestDayReport,
    RainyDaysOut,
    RainyDaysReport,
)


def _check_city(conn: Connection, cities: CityDAO, city: str | None) -> None:
    """Raise CityNotFound if a city filter is given and no such city is stored."""
    if city is not None and not cities.city_exists(conn, city):
        raise CityNotFound(city)


def average_max(
    conn: Connection,
    cities: CityDAO,
    reports: ReportDAO,
    since: date,
    city: str | None,
) -> AverageMaxReport:
    """Return the average maximum temperature per city, hottest first."""
    _check_city(conn, cities, city)
    rows = reports.average_max_temp_per_city(conn, since=since.isoformat(), city=city)
    return AverageMaxReport(
        start_date=since,
        items=[AverageMaxOut(city=name, avg_max_c=avg) for name, avg in rows],
    )


def hottest_day(
    conn: Connection,
    cities: CityDAO,
    reports: ReportDAO,
    since: date,
    city: str | None,
) -> HottestDayReport:
    """Return each city's hottest day. A tie shows every tied day."""
    _check_city(conn, cities, city)
    rows = reports.hottest_day_per_city(conn, since=since.isoformat(), city=city)
    return HottestDayReport(
        start_date=since,
        items=[
            HottestDayOut(city=name, date=day, temp_max_c=temp)
            for name, day, temp in rows
        ],
    )


def rainy_days(
    conn: Connection,
    cities: CityDAO,
    reports: ReportDAO,
    since: date,
    city: str | None,
) -> RainyDaysReport:
    """Return each city's days with precipitation above 0."""
    _check_city(conn, cities, city)
    rows = reports.rainy_days_per_city(conn, since=since.isoformat(), city=city)
    return RainyDaysReport(
        start_date=since,
        items=[RainyDaysOut(city=name, rainy_days=days) for name, days in rows],
    )
