"""The rules for reading cities. No HTTP and no SQL here."""

from api_to_sqlite.cities.dao import CityDAO
from api_to_sqlite.cities.exceptions import CityNotFound
from api_to_sqlite.cities.schemas import CityOut
from api_to_sqlite.database import Connection
from api_to_sqlite.config import CITIES


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
        cities.upsert_city(conn, name, latitude, longitude)
    conn.commit()
