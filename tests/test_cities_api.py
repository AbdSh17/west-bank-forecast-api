"""Tests for the cities endpoints, called in-process with TestClient."""

import pytest
from fastapi.testclient import TestClient

from api_to_sqlite.cities.dao import CityDAO
from api_to_sqlite.main import app


@pytest.fixture
def client() -> TestClient:
    """A client with no startup, so the app does not connect by itself."""
    return TestClient(app)


def add_city(db, name: str = "Tulkarm") -> None:
    """Store one city in the test database."""
    with db.connection() as conn:
        CityDAO().upsert_city(conn, name, 32.31, 35.03)
        conn.commit()


def test_list_is_an_object_with_an_empty_items_array(client, db):
    response = client.get("/v1/cities")
    assert response.status_code == 200
    assert response.json() == {"items": []}


def test_list_returns_the_stored_cities(client, db):
    add_city(db)
    response = client.get("/v1/cities")
    assert response.status_code == 200
    items = response.json()["items"]
    assert [item["name"] for item in items] == ["Tulkarm"]
    assert set(items[0]) == {"id", "name", "latitude", "longitude"}


def test_get_one_ignores_letter_case(client, db):
    add_city(db)
    response = client.get("/v1/cities/TULKARM")
    assert response.status_code == 200
    assert response.json()["name"] == "Tulkarm"


def test_unknown_city_answers_404_problem_json(client, db):
    response = client.get("/v1/cities/nowhere")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["title"] == "City not found"
    assert body["status"] == 404
    assert body["detail"] == "No city named 'nowhere'."
    assert body["instance"] == "/v1/cities/nowhere"
