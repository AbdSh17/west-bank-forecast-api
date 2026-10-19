"""Tests for the API, called in-process with TestClient."""

import pytest
from fastapi.testclient import TestClient

from api_to_sqlite import database
from api_to_sqlite.database import DatabaseConnectionError, get_connection
from api_to_sqlite.main import app
from api_to_sqlite.settings import get_settings


@pytest.fixture
def client() -> TestClient:
    """A client with no startup, so the app does not connect by itself."""
    return TestClient(app)


@pytest.fixture
def small_pool(monkeypatch):
    """Make the manager use a pool of one connection. Request it before db."""
    monkeypatch.setenv("MYSQL_POOL_SIZE", "1")
    get_settings.cache_clear()


@pytest.fixture
def database_down():
    """Make every request that needs a connection fail as if MySQL were down."""

    def failing():
        raise DatabaseConnectionError("down")

    app.dependency_overrides[get_connection] = failing
    yield
    app.dependency_overrides.clear()


def assert_database_unavailable(response) -> None:
    """Check the 503 answer for an unavailable database."""
    assert response.status_code == 503
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.headers["retry-after"] == "2"
    body = response.json()
    assert body["title"] == "Database unavailable"
    assert body["status"] == 503
    assert body["instance"] == "/health/ready"


def test_health_answers_without_a_database(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_answers_200_when_the_database_works(client, db):
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_ready_answers_503_when_the_database_is_down(client, database_down):
    assert_database_unavailable(client.get("/health/ready"))


def test_ready_answers_503_when_the_pool_stays_empty(
    client, small_pool, db, monkeypatch
):
    monkeypatch.setattr(database, "POOL_WAIT_SECONDS", 0.2)
    with db.connection():
        response = client.get("/health/ready")
    assert_database_unavailable(response)


def test_startup_creates_the_tables_and_seeds_the_cities(db):
    with db.connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DROP TABLE daily_weather")
        cursor.execute("DROP TABLE cities")
        conn.commit()
        cursor.close()
    with TestClient(app) as client:
        response = client.get("/v1/cities")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 5
