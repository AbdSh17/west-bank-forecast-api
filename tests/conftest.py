"""Shared fixtures for tests that use a real MySQL database."""

import pytest

from api_to_sqlite import config
from api_to_sqlite.cities.dao import CityDAO
from api_to_sqlite.database import ConnectionManager
from api_to_sqlite.forecasts.dao import ForecastDAO


@pytest.fixture
def db(monkeypatch):
    """Point the manager at the test database, empty the tables, yield the manager."""
    name = config.MYSQL_TEST_DATABASE
    if not name.endswith("_test"):
        pytest.exit(f"Refusing to run: {name!r} does not end in '_test'.")
    monkeypatch.setattr(config, "MYSQL_DATABASE", name)
    ConnectionManager.reset()
    manager = ConnectionManager()
    with manager.connection() as conn:
        CityDAO().create_schema(conn)
        ForecastDAO().create_schema(conn)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM daily_weather")
        cursor.execute("DELETE FROM cities")
        conn.commit()
        cursor.close()
    yield manager
    ConnectionManager.reset()
