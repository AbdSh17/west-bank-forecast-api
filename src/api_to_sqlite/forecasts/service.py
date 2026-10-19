"""Fetch forecasts from Open-Meteo and store them."""

from dataclasses import dataclass

from api_to_sqlite.cities.dao import CityDAO
from api_to_sqlite.config import CITIES
from api_to_sqlite.database import ConnectionManager
from api_to_sqlite.forecasts.dao import ForecastDAO
from api_to_sqlite.openmeteo.client import fetch_forecast
from api_to_sqlite.openmeteo.exceptions import FetchError
from api_to_sqlite.openmeteo.parse import parse_daily


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

    results: list[CityResult] = []
    for name, latitude, longitude in CITIES:
        try:
            records = parse_daily(fetch_forecast(latitude, longitude))
        except FetchError as error:
            results.append(CityResult(name, error=str(error)))
            continue
        with manager.connection() as conn:
            city_id = cities.upsert_city(conn, name, latitude, longitude)
            forecasts.upsert_daily_weather(conn, city_id, records)
            conn.commit()
        results.append(CityResult(name, days=len(records)))
    return results
