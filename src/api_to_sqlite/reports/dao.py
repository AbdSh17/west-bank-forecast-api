"""SQL operations for the three reports."""

from datetime import date

from api_to_sqlite.database import Connection
from api_to_sqlite.sql_loader import _query

DOMAIN = "reports"


def _today() -> str:
    """Return today's date in the machine's local timezone as YYYY-MM-DD."""
    return date.today().isoformat()


class ReportDAO:
    """Runs the report SQL on a connection that the caller supplies."""

    def average_max_temp_per_city(
        self,
        conn: Connection,
        since: str | None = None,
        city: str | None = None,
    ) -> list[tuple[str, float]]:
        """Return each city's average max temperature from `since` on, hottest first."""
        return _query(
            conn, DOMAIN, "average_max.sql", {"since": since or _today(), "city": city}
        )

    def hottest_day_per_city(
        self,
        conn: Connection,
        since: str | None = None,
        city: str | None = None,
    ) -> list[tuple[str, str, float]]:
        """Return each city's hottest day from `since` on; ties show all days."""
        return _query(
            conn, DOMAIN, "hottest_day.sql", {"since": since or _today(), "city": city}
        )

    def rainy_days_per_city(
        self,
        conn: Connection,
        since: str | None = None,
        city: str | None = None,
    ) -> list[tuple[str, int]]:
        """Return each city's days with precipitation above 0 from `since` on."""
        return _query(
            conn, DOMAIN, "rainy_days.sql", {"since": since or _today(), "city": city}
        )
