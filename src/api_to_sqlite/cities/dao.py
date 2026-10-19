"""SQL operations for the cities table."""

from api_to_sqlite.database import Connection
from api_to_sqlite.sql_loader import _execute, _query
from dataclasses import asdict
from api_to_sqlite.cities.models import NewCity

DOMAIN = "cities"


class CityDAO:
    """Runs the cities SQL on a connection that the caller supplies."""

    def create_schema(self, conn: Connection) -> None:
        """Create the cities table if it does not exist."""
        _execute(conn, DOMAIN, "create_cities.sql")

    def upsert_city(self, conn: Connection, city: NewCity) -> int:
        """Insert or update one city and return its id."""
        _execute(conn, DOMAIN, "upsert_city.sql", asdict(city))
        return _query(conn, DOMAIN, "get_city_id.sql", {"name": city.name})[0][0]

    def city_exists(self, conn: Connection, city: str) -> bool:
        """Return True if a city with this name (any letter case) is stored."""
        return len(_query(conn, DOMAIN, "city_exists.sql", {"city": city})) > 0

    def list_all(self, conn: Connection) -> list[tuple[int, str, float, float]]:
        """Return every city as (id, name, latitude, longitude), in insertion order."""
        return _query(conn, DOMAIN, "list_cities.sql")

    def get(self, conn: Connection, city: str) -> tuple[int, str, float, float] | None:
        """Return one city by name in any letter case, or None if it is unknown."""
        rows = _query(conn, DOMAIN, "get_city.sql", {"city": city})
        return rows[0] if rows else None

    def count(self, conn: Connection) -> int:
        """Return the number of stored cities."""
        return _query(conn, DOMAIN, "count_cities.sql")[0][0]

    def insert(self, conn: Connection, city: NewCity) -> int:
        """Insert a new city and return its id. A duplicate name raises IntegrityError."""
        _execute(conn, DOMAIN, "insert_city.sql", asdict(city))
        return _query(conn, DOMAIN, "get_city_id.sql", {"name": city.name})[0][0]
