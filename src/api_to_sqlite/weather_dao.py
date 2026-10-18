"""SQL operations for the weather data. All SQL lives in the sql/ folder."""

from datetime import date
from importlib.resources import files

from api_to_sqlite.config import DB_DIALECT
from api_to_sqlite.connection_manager import Connection


def _today() -> str:
    """Return today's date in the machine's local timezone as YYYY-MM-DD."""
    return date.today().isoformat()


def _load_sql(name: str) -> str:
    """Read one SQL file for the configured database dialect."""
    path = files("api_to_sqlite").joinpath("sql", DB_DIALECT, name)
    return path.read_text(encoding="utf-8")


def _query(conn: Connection, name: str, params: dict | None = None) -> list:
    """Run a SQL file and return all rows."""
    cursor = conn.cursor()
    try:
        cursor.execute(_load_sql(name), params or {})
        return cursor.fetchall()
    finally:
        cursor.close()


def _execute(conn: Connection, name: str, params: dict | None = None) -> None:
    """Run a SQL file that returns no rows."""
    cursor = conn.cursor()
    try:
        cursor.execute(_load_sql(name), params or {})
    finally:
        cursor.close()


def _execute_many(conn: Connection, name: str, rows: list[dict]) -> None:
    """Run a SQL file once for every parameter dictionary in rows."""
    cursor = conn.cursor()
    try:
        cursor.executemany(_load_sql(name), rows)
    finally:
        cursor.close()


class WeatherDAO:
    """Runs the weather SQL on a connection that the caller supplies."""

    def create_schema(self, conn: Connection) -> None:
        """Create the cities and daily_weather tables if they do not exist."""
        _execute(conn, "create_cities.sql")
        _execute(conn, "create_daily_weather.sql")

    def has_data(self, conn: Connection) -> bool:
        """Return True if at least one daily forecast row is stored."""
        return _query(conn, "has_data.sql")[0][0] > 0

    def upsert_city(
        self,
        conn: Connection,
        name: str,
        latitude: float,
        longitude: float,
    ) -> int:
        """Insert or update one city and return its id."""
        _execute(
            conn,
            "upsert_city.sql",
            {"name": name, "latitude": latitude, "longitude": longitude},
        )
        return _query(conn, "get_city_id.sql", {"name": name})[0][0]

    def upsert_daily_weather(
        self, conn: Connection, city_id: int, records: list[dict]
    ) -> None:
        """Insert or update the daily forecast rows for one city."""
        _execute_many(
            conn,
            "upsert_daily_weather.sql",
            [
                {**record, "city_id": city_id} for record in records
            ],  # records: record of N day forecast
        )

    def city_exists(self, conn: Connection, city: str) -> bool:
        """Return True if a city with this name (any letter case) is stored."""
        return len(_query(conn, "city_exists.sql", {"city": city})) > 0

    def average_max_temp_per_city(
        self,
        conn: Connection,
        since: str | None = None,
        city: str | None = None,
    ) -> list[tuple[str, float]]:
        """Return each city's average max temperature from `since` on, hottest first."""
        return _query(
            conn, "average_max.sql", {"since": since or _today(), "city": city}
        )

    def hottest_day_per_city(
        self,
        conn: Connection,
        since: str | None = None,
        city: str | None = None,
    ) -> list[tuple[str, str, float]]:
        """Return each city's hottest day from `since` on; ties show all days."""
        return _query(
            conn, "hottest_day.sql", {"since": since or _today(), "city": city}
        )

    def rainy_days_per_city(
        self,
        conn: Connection,
        since: str | None = None,
        city: str | None = None,
    ) -> list[tuple[str, int]]:
        """Return each city's days with precipitation above 0 from `since` on."""
        return _query(
            conn, "rainy_days.sql", {"since": since or _today(), "city": city}
        )
