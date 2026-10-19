"""Tests for the error handlers, on a small app with no database."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api_to_sqlite.cities.exceptions import CityAlreadyExists, CityNotFound
from api_to_sqlite.database import DatabaseConnectionError
from api_to_sqlite.errors import register_error_handlers

RAISED = {
    "/boom": KeyError("secret detail"),
    "/no-city": CityNotFound("x"),
    "/duplicate": CityAlreadyExists("x"),
    "/no-db": DatabaseConnectionError("down"),
}


@pytest.fixture
def client() -> TestClient:
    """An app whose routes raise one known error each."""
    app = FastAPI()
    register_error_handlers(app)

    for path, error in RAISED.items():

        def route(error=error):
            raise error

        app.get(path)(route)

    return TestClient(app, raise_server_exceptions=False)


@pytest.mark.parametrize(
    "path, status",
    [("/boom", 500), ("/no-city", 404), ("/duplicate", 409), ("/no-db", 503)],
)
def test_each_error_has_its_status_and_problem_json(client, path, status):
    response = client.get(path)
    assert response.status_code == status
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["status"] == status
    assert response.json()["instance"] == path


def test_an_unexpected_error_does_not_leak_its_message(client):
    body = client.get("/boom").json()
    assert body["title"] == "Internal server error"
    assert "secret detail" not in str(body)


def test_database_unavailable_asks_the_client_to_retry(client):
    assert client.get("/no-db").headers["retry-after"] == "2"
