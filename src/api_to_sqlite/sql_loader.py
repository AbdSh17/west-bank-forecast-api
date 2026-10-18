"""SQL operations for the weather data. All SQL lives in the sql/ folder."""

from importlib.resources import files

from api_to_sqlite.database import Connection


def _load_sql(domain: str, name: str) -> str:
    """Read one SQL file from the sql/ folder of a domain package."""
    path = files(f"api_to_sqlite.{domain}").joinpath("sql", name)
    return path.read_text(encoding="utf-8")


def _query(
    conn: Connection, domain: str, name: str, params: dict | None = None
) -> list:
    """Run a SQL file and return all rows."""
    cursor = conn.cursor()
    try:
        cursor.execute(_load_sql(domain, name), params or {})
        return cursor.fetchall()
    finally:
        cursor.close()


def _execute(
    conn: Connection, domain: str, name: str, params: dict | None = None
) -> None:
    """Run a SQL file that returns no rows."""
    cursor = conn.cursor()
    try:
        cursor.execute(_load_sql(domain, name), params or {})
    finally:
        cursor.close()


def _execute_many(conn: Connection, domain: str, name: str, rows: list[dict]) -> None:
    """Run a SQL file once for every parameter dictionary in rows."""
    cursor = conn.cursor()
    try:
        cursor.executemany(_load_sql(domain, name), rows)
    finally:
        cursor.close()
