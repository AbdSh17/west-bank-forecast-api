"""The cities endpoints."""

from fastapi import APIRouter, Depends

from api_to_sqlite.cities import service
from api_to_sqlite.cities.dao import CityDAO
from api_to_sqlite.cities.schemas import CityList, CityOut
from api_to_sqlite.database import Connection, get_connection

router = APIRouter(prefix="/v1/cities", tags=["cities"])


@router.get("")
def list_cities(
    conn: Connection = Depends(get_connection),
    cities: CityDAO = Depends(CityDAO),
) -> CityList:
    """List every city."""
    return CityList(items=service.list_cities(conn, cities))


@router.get("/{city}")
def get_city(
    city: str,
    conn: Connection = Depends(get_connection),
    cities: CityDAO = Depends(CityDAO),
) -> CityOut:
    """Return one city by name, in any letter case."""
    return service.get_city(conn, cities, city)
