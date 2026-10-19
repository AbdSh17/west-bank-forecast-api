"""Fetch forecasts from Open-Meteo and store them."""

from dataclasses import dataclass

from api_to_sqlite.cities.dao import CityDAO
from api_to_sqlite.cities import service as city_service
from api_to_sqlite.database import ConnectionManager
from api_to_sqlite.forecasts.dao import ForecastDAO
from api_to_sqlite.openmeteo.client import fetch_forecast
from api_to_sqlite.openmeteo.exceptions import FetchError
from api_to_sqlite.openmeteo.parse import parse_daily
from api_to_sqlite.cities.models import NewCity
from api_to_sqlite.cities.exceptions import CityNotFound
from api_to_sqlite.forecasts.models import ForecastFilter, Page
from api_to_sqlite.forecasts.schemas import ForecastList, ForecastOut


@dataclass
class CityResult:
    """The outcome of refreshing one city. An error of None means it was stored."""

    city: str
    days: int = 0
    error: str | None = None


def refresh(
    manager: ConnectionManager,
    cities: CityDAO,
    forecasts: ForecastDAO,
) -> list[CityResult]:
    """Fetch every city, store the successes and return one result per city."""
    with manager.connection() as conn:
        cities.create_schema(conn)
        forecasts.create_schema(conn)
        city_service.seed_cities(conn, cities)
        stored = cities.list_all(conn)

    results: list[CityResult] = []
    for _, name, latitude, longitude in stored:
        try:
            records = parse_daily(fetch_forecast(latitude, longitude))
        except FetchError as error:
            results.append(CityResult(name, error=str(error)))
            continue
        with manager.connection() as conn:
            city_id = cities.upsert_city(conn, NewCity(name, latitude, longitude))
            forecasts.upsert_daily_weather(conn, city_id, records)
            conn.commit()
        results.append(CityResult(name, days=len(records)))
    return results


def list_forecasts(
    conn: Connection,
    cities: CityDAO,
    forecasts: ForecastDAO,
    filters: ForecastFilter,
    page: Page,
) -> ForecastList:
    """Return one page of forecasts. Raise CityNotFound for an unknown city filter."""
    if filters.city is not None and not cities.city_exists(conn, filters.city):
        raise CityNotFound(filters.city)
    rows = forecasts.list_forecasts(conn, filters, page)
    return ForecastList(
        items=[
            ForecastOut(
                city=city,
                date=day,
                temp_max_c=temp_max,
                temp_min_c=temp_min,
                precipitation_mm=precipitation,
            )
            for city, day, temp_max, temp_min, precipitation in rows
        ],
        limit=page.limit,
        offset=page.offset,
        total=forecasts.count_forecasts(conn, filters),
    )
