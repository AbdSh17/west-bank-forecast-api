"""SQL operations for the daily_weather table."""

from api_to_sqlite.database import Connection
from api_to_sqlite.sql_loader import _execute, _execute_many, _query

DOMAIN = "forecasts"


class ForecastDAO:
    """Runs the forecast SQL on a connection that the caller supplies."""

    def create_schema(self, conn: Connection) -> None:
        """Create the daily_weather table if it does not exist."""
        _execute(conn, DOMAIN, "create_daily_weather.sql")

    def has_data(self, conn: Connection) -> bool:
        """Return True if at least one daily forecast row is stored."""
        return _query(conn, DOMAIN, "has_data.sql")[0][0] > 0

    def upsert_daily_weather(
        self, conn: Connection, city_id: int, records: list[dict]
    ) -> None:
        """Insert or update the daily forecast rows for one city."""
        _execute_many(
            conn,
            DOMAIN,
            "upsert_daily_weather.sql",
            [{**record, "city_id": city_id} for record in records],
        )
