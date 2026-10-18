"""SQL operations for the cities table."""

from api_to_sqlite.database import Connection
from api_to_sqlite.sql_loader import _execute, _query

DOMAIN = "cities"


class CityDAO:
    """Runs the cities SQL on a connection that the caller supplies."""

    def create_schema(self, conn: Connection) -> None:
        """Create the cities table if it does not exist."""
        _execute(conn, DOMAIN, "create_cities.sql")

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
            DOMAIN,
            "upsert_city.sql",
            {"name": name, "latitude": latitude, "longitude": longitude},
        )
        return _query(conn, DOMAIN, "get_city_id.sql", {"name": name})[0][0]

    def city_exists(self, conn: Connection, city: str) -> bool:
        """Return True if a city with this name (any letter case) is stored."""
        return len(_query(conn, DOMAIN, "city_exists.sql", {"city": city})) > 0
