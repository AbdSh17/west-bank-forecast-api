"""Tests for the forecasts feature: the DAO, the service and GET /v1/forecasts."""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from api_to_sqlite.cities.dao import CityDAO
from api_to_sqlite.cities.exceptions import CityNotFound
from api_to_sqlite.cities.models import NewCity
from api_to_sqlite.forecasts import service
from api_to_sqlite.forecasts.dao import ForecastDAO
from api_to_sqlite.forecasts.models import ForecastFilter, Page
from api_to_sqlite.main import app

RECORDS = [
    {"date": "2026-10-23", "temp_max": 30.0, "temp_min": 20.0, "precipitation": 0.0},
    {"date": "2026-10-24", "temp_max": 28.0, "temp_min": 18.0, "precipitation": 2.5},
]

TULKARM = NewCity("Tulkarm", 32.31, 35.03)
QALQILYA = NewCity("Qalqilya", 32.19, 34.97)
SINCE = "2026-10-01"


@pytest.fixture
def client() -> TestClient:
    """A client with no startup, so the app does not connect by itself."""
    return TestClient(app)


def store_forecasts(db, *cities: NewCity) -> None:
    """Store the two RECORDS days for each given city."""
    city_dao, forecast_dao = CityDAO(), ForecastDAO()
    with db.connection() as conn:
        for city in cities:
            city_id = city_dao.upsert_city(conn, city)
            forecast_dao.upsert_daily_weather(conn, city_id, RECORDS)
        conn.commit()


# --- the DAO ---------------------------------------------------------------


def test_dao_rows_carry_the_city_name_and_come_in_date_order(db):
    store_forecasts(db, TULKARM)
    with db.connection() as conn:
        rows = ForecastDAO().list_forecasts(conn, ForecastFilter(SINCE), Page())
    assert [(row[0], str(row[1]), row[2]) for row in rows] == [
        ("Tulkarm", "2026-10-23", 30.0),
        ("Tulkarm", "2026-10-24", 28.0),
    ]


def test_dao_end_date_is_inclusive(db):
    store_forecasts(db, TULKARM)
    filters = ForecastFilter(SINCE, end_date="2026-10-23")
    with db.connection() as conn:
        rows = ForecastDAO().list_forecasts(conn, filters, Page())
    assert [str(row[1]) for row in rows] == ["2026-10-23"]


def test_dao_city_filter_ignores_letter_case(db):
    store_forecasts(db, TULKARM, QALQILYA)
    filters = ForecastFilter(SINCE, city="TULKARM")
    with db.connection() as conn:
        rows = ForecastDAO().list_forecasts(conn, filters, Page())
    assert {row[0] for row in rows} == {"Tulkarm"}


def test_dao_paging_changes_the_rows_but_not_the_total(db):
    store_forecasts(db, TULKARM, QALQILYA)
    forecasts, filters = ForecastDAO(), ForecastFilter(SINCE)
    with db.connection() as conn:
        page = forecasts.list_forecasts(conn, filters, Page(limit=1, offset=1))
        total = forecasts.count_forecasts(conn, filters)
    assert len(page) == 1
    assert total == 4


# --- the service -----------------------------------------------------------


def test_service_returns_a_page_with_the_paging_numbers(db):
    store_forecasts(db, TULKARM, QALQILYA)
    with db.connection() as conn:
        result = service.list_forecasts(
            conn,
            CityDAO(),
            ForecastDAO(),
            ForecastFilter(SINCE),
            Page(limit=3, offset=1),
        )
    assert len(result.items) == 3
    assert (result.limit, result.offset, result.total) == (3, 1, 4)
    assert result.items[0].city == "Tulkarm"


def test_service_raises_for_an_unknown_city(db):
    with db.connection() as conn:
        with pytest.raises(CityNotFound):
            service.list_forecasts(
                conn,
                CityDAO(),
                ForecastDAO(),
                ForecastFilter(SINCE, city="nowhere"),
                Page(),
            )


def test_service_returns_an_empty_page_for_a_city_without_forecasts(db):
    with db.connection() as conn:
        CityDAO().upsert_city(conn, TULKARM)
        conn.commit()
        result = service.list_forecasts(
            conn,
            CityDAO(),
            ForecastDAO(),
            ForecastFilter(SINCE, city="tulkarm"),
            Page(),
        )
    assert result.items == []
    assert result.total == 0


# --- the endpoint ----------------------------------------------------------


def test_api_returns_items_with_the_paging_numbers(client, db):
    store_forecasts(db, TULKARM)
    response = client.get("/v1/forecasts", params={"start_date": SINCE})
    assert response.status_code == 200
    body = response.json()
    assert (body["limit"], body["offset"], body["total"]) == (50, 0, 2)
    assert set(body["items"][0]) == {
        "city",
        "date",
        "temp_max_c",
        "temp_min_c",
        "precipitation_mm",
    }
    assert body["items"][0]["date"] == "2026-10-23"


def test_api_limit_and_offset_pick_the_page(client, db):
    store_forecasts(db, TULKARM, QALQILYA)
    response = client.get(
        "/v1/forecasts", params={"start_date": SINCE, "limit": 1, "offset": 1}
    )
    body = response.json()
    assert [(item["city"], item["date"]) for item in body["items"]] == [
        ("Tulkarm", "2026-10-24")
    ]
    assert body["total"] == 4


def test_api_city_filter_ignores_letter_case(client, db):
    store_forecasts(db, TULKARM, QALQILYA)
    response = client.get(
        "/v1/forecasts", params={"start_date": SINCE, "city": "QALQILYA"}
    )
    assert {item["city"] for item in response.json()["items"]} == {"Qalqilya"}


def test_api_unknown_city_answers_404_problem_json(client, db):
    response = client.get("/v1/forecasts", params={"city": "nowhere"})
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["detail"] == "No city named 'nowhere'."
    assert body["instance"] == "/v1/forecasts"


@pytest.mark.parametrize(
    "query", ["limit=0", "limit=201", "offset=-1", "start_date=not-a-date"]
)
def test_api_invalid_parameters_answer_422_problem_json(client, db, query):
    response = client.get(f"/v1/forecasts?{query}")
    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["title"] == "Validation error"


def test_api_start_date_defaults_to_today(client, db):
    today = date.today()
    records = [
        {
            "date": (today - timedelta(days=1)).isoformat(),
            "temp_max": 20.0,
            "temp_min": 10.0,
            "precipitation": 0.0,
        },
        {
            "date": today.isoformat(),
            "temp_max": 21.0,
            "temp_min": 11.0,
            "precipitation": 0.0,
        },
    ]
    with db.connection() as conn:
        city_id = CityDAO().upsert_city(conn, TULKARM)
        ForecastDAO().upsert_daily_weather(conn, city_id, records)
        conn.commit()
    body = client.get("/v1/forecasts").json()
    assert [item["date"] for item in body["items"]] == [today.isoformat()]
    assert body["total"] == 1


def test_api_end_date_before_start_date_gives_an_empty_page(client, db):
    store_forecasts(db, TULKARM)
    response = client.get(
        "/v1/forecasts", params={"start_date": "2026-10-24", "end_date": "2026-10-23"}
    )
    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["total"] == 0


def test_api_empty_database_gives_an_empty_page(client, db):
    response = client.get("/v1/forecasts")
    assert response.status_code == 200
    assert response.json() == {"items": [], "limit": 50, "offset": 0, "total": 0}
