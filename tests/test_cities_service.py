"""Tests for the cities service against the real weather_test database."""

import pytest

from api_to_sqlite.cities import service
from api_to_sqlite.cities.dao import CityDAO
from api_to_sqlite.cities.exceptions import CityAlreadyExists, CityNotFound
from api_to_sqlite.cities.models import NewCity
from api_to_sqlite.cities.schemas import CityOut
from api_to_sqlite.config import CITIES


def add_city(db, name: str = "Tulkarm") -> None:
    """Store one city in the test database."""
    with db.connection() as conn:
        CityDAO().upsert_city(conn, NewCity(name, 32.31, 35.03))
        conn.commit()


def test_list_cities_returns_city_objects(db):
    add_city(db)
    with db.connection() as conn:
        result = service.list_cities(conn, CityDAO())
    assert [city.name for city in result] == ["Tulkarm"]
    assert isinstance(result[0], CityOut)


def test_get_city_returns_the_stored_name_for_any_letter_case(db):
    add_city(db)
    with db.connection() as conn:
        city = service.get_city(conn, CityDAO(), "TULKARM")
    assert city.name == "Tulkarm"
    assert city.latitude == 32.31


def test_get_city_raises_for_an_unknown_city(db):
    with db.connection() as conn:
        with pytest.raises(CityNotFound) as error:
            service.get_city(conn, CityDAO(), "nowhere")
    assert error.value.name == "nowhere"


def test_seed_fills_an_empty_table(db):
    with db.connection() as conn:
        service.seed_cities(conn, CityDAO())
        assert CityDAO().count(conn) == len(CITIES)


def test_seed_does_nothing_when_a_city_exists(db):
    add_city(db)
    with db.connection() as conn:
        service.seed_cities(conn, CityDAO())
        assert CityDAO().count(conn) == 1


def test_create_city_stores_it_and_returns_it(db):
    with db.connection() as conn:
        created = service.create_city(conn, CityDAO(), NewCity("Tulkarm", 32.31, 35.03))
    assert created.name == "Tulkarm"
    with db.connection() as conn:
        assert service.get_city(conn, CityDAO(), "tulkarm").id == created.id


def test_create_city_twice_raises_city_already_exists(db):
    add_city(db)
    with db.connection() as conn:
        with pytest.raises(CityAlreadyExists) as error:
            service.create_city(conn, CityDAO(), NewCity("Tulkarm", 0, 0))
    assert error.value.name == "Tulkarm"


def test_create_city_with_another_letter_case_is_a_duplicate(db):
    add_city(db)
    with db.connection() as conn:
        with pytest.raises(CityAlreadyExists):
            service.create_city(conn, CityDAO(), NewCity("TULKARM", 0, 0))
