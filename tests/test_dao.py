"""Tests for the DAOs against the real weather_test database."""

import mysql.connector
import pytest

from api_to_sqlite.cities.dao import CityDAO
from api_to_sqlite.cities.models import NewCity
from api_to_sqlite.forecasts.dao import ForecastDAO
from api_to_sqlite.reports.dao import ReportDAO

RECORDS = [
    {"date": "2026-10-23", "temp_max": 30.0, "temp_min": 20.0, "precipitation": 0.0},
    {"date": "2026-10-24", "temp_max": 28.0, "temp_min": 18.0, "precipitation": 2.5},
]

TULKARM = NewCity("Tulkarm", 32.31, 35.03)
QALQILYA = NewCity("Qalqilya", 32.19, 34.97)


def test_upsert_city_returns_the_same_id_twice(db):
    cities = CityDAO()
    with db.connection() as conn:
        first = cities.upsert_city(conn, TULKARM)
        second = cities.upsert_city(conn, TULKARM)
        conn.commit()
    assert first == second


def test_city_exists_ignores_letter_case(db):
    cities = CityDAO()
    with db.connection() as conn:
        cities.upsert_city(conn, TULKARM)
        conn.commit()
        assert cities.city_exists(conn, "TULKARM")
        assert not cities.city_exists(conn, "nowhere")


def test_has_data_is_false_on_an_empty_database(db):
    with db.connection() as conn:
        assert ForecastDAO().has_data(conn) is False


def test_second_upsert_does_not_duplicate_rows(db):
    cities, forecasts = CityDAO(), ForecastDAO()
    with db.connection() as conn:
        city_id = cities.upsert_city(conn, TULKARM)
        forecasts.upsert_daily_weather(conn, city_id, RECORDS)
        forecasts.upsert_daily_weather(conn, city_id, RECORDS)
        conn.commit()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM daily_weather")
        assert cursor.fetchone()[0] == 2
        cursor.close()


def test_rainy_days_counts_only_precipitation_above_zero(db):
    cities, forecasts = CityDAO(), ForecastDAO()
    with db.connection() as conn:
        city_id = cities.upsert_city(conn, TULKARM)
        forecasts.upsert_daily_weather(conn, city_id, RECORDS)
        conn.commit()
        rows = ReportDAO().rainy_days_per_city(conn, since="2026-10-01")
    assert rows == [("Tulkarm", 1)]


def test_list_all_returns_cities_in_insertion_order(db):
    cities = CityDAO()
    with db.connection() as conn:
        cities.upsert_city(conn, TULKARM)
        cities.upsert_city(conn, QALQILYA)
        conn.commit()
        rows = cities.list_all(conn)
    assert [row[1] for row in rows] == ["Tulkarm", "Qalqilya"]


def test_get_ignores_letter_case(db):
    cities = CityDAO()
    with db.connection() as conn:
        cities.upsert_city(conn, TULKARM)
        conn.commit()
        row = cities.get(conn, "TULKARM")
    assert row is not None
    assert row[1:] == ("Tulkarm", 32.31, 35.03)


def test_get_returns_none_for_an_unknown_city(db):
    with db.connection() as conn:
        assert CityDAO().get(conn, "nowhere") is None


def test_insert_returns_the_new_id(db):
    cities = CityDAO()
    with db.connection() as conn:
        city_id = cities.insert(conn, TULKARM)
        assert cities.get(conn, "Tulkarm")[0] == city_id


def test_insert_twice_raises_a_duplicate_key_error(db):
    cities = CityDAO()
    with db.connection() as conn:
        cities.insert(conn, TULKARM)
        with pytest.raises(mysql.connector.IntegrityError) as error:
            cities.insert(conn, TULKARM)
    assert error.value.errno == 1062


def test_insert_treats_a_different_letter_case_as_a_duplicate(db):
    cities = CityDAO()
    with db.connection() as conn:
        cities.insert(conn, TULKARM)
        with pytest.raises(mysql.connector.IntegrityError):
            cities.insert(conn, NewCity("TULKARM", 32.31, 35.03))
