"""Tests for the report endpoints and POST /v1/forecast-refreshes."""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from api_to_sqlite.cities.dao import CityDAO
from api_to_sqlite.cities.models import NewCity
from api_to_sqlite.forecasts import service
from api_to_sqlite.forecasts.dao import ForecastDAO
from api_to_sqlite.main import app
from api_to_sqlite.openmeteo.exceptions import FetchError

TODAY = date.today()
TULKARM = NewCity("Tulkarm", 32.31, 35.03)
QALQILYA = NewCity("Qalqilya", 32.19, 34.97)


def record(offset_days: int, temp_max: float, rain: float = 0.0) -> dict:
    """One daily record, offset_days from today."""
    return {
        "date": (TODAY + timedelta(days=offset_days)).isoformat(),
        "temp_max": temp_max,
        "temp_min": temp_max - 10,
        "precipitation": rain,
    }


@pytest.fixture
def client() -> TestClient:
    """A client with no startup, so the app does not connect by itself."""
    return TestClient(app)


@pytest.fixture
def stored(db):
    """Tulkarm and Qalqilya, two days each. Tulkarm has one rainy day."""
    with db.connection() as conn:
        for city, records in (
            (TULKARM, [record(0, 30.0), record(1, 34.0, rain=2.0)]),
            (QALQILYA, [record(0, 25.0), record(1, 25.0)]),
        ):
            city_id = CityDAO().upsert_city(conn, city)
            ForecastDAO().upsert_daily_weather(conn, city_id, records)
        conn.commit()


def fake_forecast(latitude: float, longitude: float) -> dict:
    """Return 7 days starting today, like the real API."""
    days = [TODAY + timedelta(days=i) for i in range(7)]
    return {
        "daily": {
            "time": [day.isoformat() for day in days],
            "temperature_2m_max": [30.0] * 7,
            "temperature_2m_min": [20.0] * 7,
            "precipitation_sum": [0.0] * 7,
        }
    }


def failing_for(*latitudes: float):
    """A fake that fails for the cities with the given latitudes."""

    def fake(latitude: float, longitude: float) -> dict:
        if latitude in latitudes:
            raise FetchError("The service is overloaded")
        return fake_forecast(latitude, longitude)

    return fake


# --- reports ---------------------------------------------------------------


def test_average_max_is_ordered_hottest_first(client, stored):
    response = client.get("/v1/reports/average-max")
    assert response.status_code == 200
    body = response.json()
    assert body["start_date"] == TODAY.isoformat()
    assert body["items"] == [
        {"city": "Tulkarm", "avg_max_c": 32.0},
        {"city": "Qalqilya", "avg_max_c": 25.0},
    ]


def test_hottest_day_shows_every_tied_day(client, stored):
    items = client.get("/v1/reports/hottest-day").json()["items"]
    by_city = {}
    for item in items:
        by_city.setdefault(item["city"], []).append(item["date"])
    assert by_city["Tulkarm"] == [(TODAY + timedelta(days=1)).isoformat()]
    assert len(by_city["Qalqilya"]) == 2


def test_rainy_days_counts_only_rain(client, stored):
    items = client.get("/v1/reports/rainy-days").json()["items"]
    assert {item["city"]: item["rainy_days"] for item in items} == {
        "Qalqilya": 0,
        "Tulkarm": 1,
    }


@pytest.mark.parametrize("report", ["average-max", "hottest-day", "rainy-days"])
def test_report_city_filter_ignores_letter_case(client, stored, report):
    items = client.get(f"/v1/reports/{report}", params={"city": "TULKARM"}).json()[
        "items"
    ]
    assert {item["city"] for item in items} == {"Tulkarm"}


@pytest.mark.parametrize("report", ["average-max", "hottest-day", "rainy-days"])
def test_report_unknown_city_answers_404_problem_json(client, db, report):
    response = client.get(f"/v1/reports/{report}", params={"city": "nowhere"})
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["instance"] == f"/v1/reports/{report}"


@pytest.mark.parametrize("report", ["average-max", "hottest-day", "rainy-days"])
def test_report_bad_date_answers_422_problem_json(client, db, report):
    response = client.get(f"/v1/reports/{report}", params={"start_date": "not-a-date"})
    assert response.status_code == 422
    assert response.json()["title"] == "Validation error"


def test_report_start_date_defaults_to_today_and_can_move_forward(client, stored):
    tomorrow = (TODAY + timedelta(days=1)).isoformat()
    body = client.get("/v1/reports/rainy-days", params={"start_date": tomorrow}).json()
    assert body["start_date"] == tomorrow
    assert {item["city"]: item["rainy_days"] for item in body["items"]}["Tulkarm"] == 1
    future = (TODAY + timedelta(days=30)).isoformat()
    assert client.get("/v1/reports/average-max", params={"start_date": future}).json()[
        "items"
    ] == []


def test_report_on_an_empty_database_gives_an_empty_list(client, db):
    assert client.get("/v1/reports/average-max").json()["items"] == []


# --- refresh ---------------------------------------------------------------


def test_refresh_stores_every_city_and_answers_200(client, db, monkeypatch):
    monkeypatch.setattr(service, "fetch_forecast", fake_forecast)
    response = client.post("/v1/forecast-refreshes")
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) == 5
    assert all(r == {"city": r["city"], "status": "stored", "days": 7} for r in results)
    assert client.get("/v1/forecasts").json()["total"] == 35


def test_refresh_with_one_failure_answers_207(client, db, monkeypatch):
    monkeypatch.setattr(service, "fetch_forecast", failing_for(32.46))
    response = client.post("/v1/forecast-refreshes")
    assert response.status_code == 207
    by_city = {r["city"]: r for r in response.json()["results"]}
    assert by_city["Jenin"] == {
        "city": "Jenin",
        "status": "failed",
        "error": "The service is overloaded",
    }
    assert by_city["Nablus"]["status"] == "stored"
    assert client.get("/v1/forecasts").json()["total"] == 28


def test_refresh_with_every_failure_answers_502(client, db, monkeypatch):
    monkeypatch.setattr(
        service, "fetch_forecast", failing_for(31.90, 32.22, 31.53, 32.46, 31.86)
    )
    response = client.post("/v1/forecast-refreshes")
    assert response.status_code == 502
    assert {r["status"] for r in response.json()["results"]} == {"failed"}
    assert client.get("/v1/forecasts").json()["total"] == 0


def test_a_second_refresh_does_not_duplicate_rows(client, db, monkeypatch):
    monkeypatch.setattr(service, "fetch_forecast", fake_forecast)
    client.post("/v1/forecast-refreshes")
    client.post("/v1/forecast-refreshes")
    assert client.get("/v1/forecasts").json()["total"] == 35


def test_refresh_fetches_a_city_added_through_the_api(client, db, monkeypatch):
    monkeypatch.setattr(service, "fetch_forecast", fake_forecast)
    client.post("/v1/forecast-refreshes")
    created = client.post(
        "/v1/cities", json={"name": "Tulkarm", "latitude": 32.31, "longitude": 35.03}
    )
    assert created.status_code == 201
    response = client.post("/v1/forecast-refreshes")
    assert len(response.json()["results"]) == 6
    assert client.get("/v1/forecasts", params={"city": "tulkarm"}).json()["total"] == 7


def test_refresh_answers_405_for_get(client, db):
    assert client.get("/v1/forecast-refreshes").status_code == 405
