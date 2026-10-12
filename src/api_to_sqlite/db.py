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
