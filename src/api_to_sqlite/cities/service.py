"""The rules for reading cities. No HTTP and no SQL here."""

import mysql.connector
from api_to_sqlite.cities.dao import CityDAO
from api_to_sqlite.cities.exceptions import CityNotFound
from api_to_sqlite.cities.schemas import CityOut
from api_to_sqlite.database import Connection
from api_to_sqlite.config import CITIES
from api_to_sqlite.cities.models import NewCity
from api_to_sqlite.cities.exceptions import CityAlreadyExists, CityNotFound


def list_cities(conn: Connection, cities: CityDAO) -> list[CityOut]:
    """Return every city in insertion order."""
    return [
        CityOut(id=id_, name=name, latitude=latitude, longitude=longitude)
        for id_, name, latitude, longitude in cities.list_all(conn)
    ]


def get_city(conn: Connection, cities: CityDAO, name: str) -> CityOut:
    """Return one city by name in any letter case, or raise CityNotFound."""
    row = cities.get(conn, name)
    if row is None:
        raise CityNotFound(name)
    id_, found_name, latitude, longitude = row
    return CityOut(id=id_, name=found_name, latitude=latitude, longitude=longitude)


def seed_cities(conn: Connection, cities: CityDAO) -> None:
    """Copy the cities from config into an empty table. Do nothing otherwise."""
    if cities.count(conn) > 0:
        return
    for name, latitude, longitude in CITIES:
        cities.upsert_city(conn, NewCity(name, latitude, longitude))
    conn.commit()


DUPLICATE_KEY_ERRNO = 1062


def create_city(conn: Connection, cities: CityDAO, city: NewCity) -> CityOut:
    """Store a new city and return it. Raise CityAlreadyExists on a duplicate name."""
    try:
        cities.insert(conn, city)
    except mysql.connector.IntegrityError as error:
        if error.errno == DUPLICATE_KEY_ERRNO:
            raise CityAlreadyExists(city.name) from error
        raise
    conn.commit()
    return get_city(conn, cities, city.name)
