"""SQLite schema, inserts and queries for the weather data."""

import sqlite3
from pathlib import Path

from api_to_sqlite.config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS cities (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS daily_weather (
    city_id INTEGER NOT NULL REFERENCES cities(id),
    date TEXT NOT NULL,
    temp_max REAL,
    temp_min REAL,
    precipitation REAL,
    PRIMARY KEY (city_id, date)
);
"""


def connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Open the database, creating its folder, with foreign keys enforced."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_schema(conn: sqlite3.Connection) -> None:
    """Create the cities and daily_weather tables if they do not exist."""
    conn.executescript(SCHEMA)


def upsert_city(
    conn: sqlite3.Connection, name: str, latitude: float, longitude: float
) -> int:
    """Insert or update one city and return its id."""
    conn.execute(
        """
        INSERT INTO cities (name, latitude, longitude)
        VALUES (?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET
            latitude = excluded.latitude,
            longitude = excluded.longitude
        """,
        (name, latitude, longitude),
    )
    row = conn.execute("SELECT id FROM cities WHERE name = ?", (name,)).fetchone()
    return row[0]


def upsert_daily_weather(
    conn: sqlite3.Connection, city_id: int, records: list[dict]
) -> None:
    """Insert or update the daily forecast rows for one city."""
    conn.executemany(
        """
        INSERT INTO daily_weather
            (city_id, date, temp_max, temp_min, precipitation)
        VALUES
            (:city_id, :date, :temp_max, :temp_min, :precipitation)
        ON CONFLICT(city_id, date) DO UPDATE SET
            temp_max = excluded.temp_max,
            temp_min = excluded.temp_min,
            precipitation = excluded.precipitation
        """,
        [{**record, "city_id": city_id} for record in records],
    )


def average_max_temp_per_city(conn: sqlite3.Connection) -> list[tuple[str, float]]:
    """Return each city with its average max temperature, hottest first."""
    return conn.execute("""
        SELECT c.name, ROUND(AVG(w.temp_max), 1) AS avg_max
        FROM cities AS c
        JOIN daily_weather AS w ON w.city_id = c.id
        GROUP BY c.id
        ORDER BY avg_max DESC
        """).fetchall()


def hottest_day_per_city(conn: sqlite3.Connection) -> list[tuple[str, str, float]]:
    """Return each city's hottest day (date and max temperature); ties show all days."""
    return conn.execute("""
        SELECT c.name, w.date, w.temp_max
        FROM cities AS c
        JOIN daily_weather AS w ON w.city_id = c.id
        WHERE w.temp_max = (
            SELECT MAX(temp_max)
            FROM daily_weather
            WHERE city_id = c.id
        )
        ORDER BY w.temp_max DESC, c.name, w.date
        """).fetchall()


def rainy_days_per_city(conn: sqlite3.Connection) -> list[tuple[str, int]]:
    """Return each city with its number of days with precipitation above 0."""
    return conn.execute("""
        SELECT c.name, COUNT(w.date) AS rainy_days
        FROM cities AS c
        LEFT JOIN daily_weather AS w
            ON w.city_id = c.id AND w.precipitation > 0
        GROUP BY c.id
        ORDER BY rainy_days DESC, c.name
        """).fetchall()
