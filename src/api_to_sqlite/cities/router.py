"""The cities endpoints."""

from fastapi import APIRouter, Depends, Response, status

from api_to_sqlite.cities import service
from api_to_sqlite.cities.dao import CityDAO
from api_to_sqlite.cities.schemas import CityCreate, CityList, CityOut
from api_to_sqlite.database import Connection, get_connection
from urllib.parse import quote
from api_to_sqlite.cities.models import NewCity
from api_to_sqlite.api_docs import (
    CITY_ALREADY_EXISTS,
    CITY_NOT_FOUND,
    DATABASE_UNAVAILABLE,
    VALIDATION_ERROR,
)

router = APIRouter(prefix="/v1/cities", tags=["cities"])


@router.get("", summary="List the cities", responses={**DATABASE_UNAVAILABLE})
def list_cities(
    conn: Connection = Depends(get_connection),
    cities: CityDAO = Depends(CityDAO),
) -> CityList:
    """List every city."""
    return CityList(items=service.list_cities(conn, cities))


@router.get(
    "/{city}",
    summary="Get one city",
    responses={**CITY_NOT_FOUND, **DATABASE_UNAVAILABLE},
)
def get_city(
    city: str,
    conn: Connection = Depends(get_connection),
    cities: CityDAO = Depends(CityDAO),
) -> CityOut:
    """Return one city by name, in any letter case."""
    return service.get_city(conn, cities, city)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Add a city",
    responses={**CITY_ALREADY_EXISTS, **VALIDATION_ERROR, **DATABASE_UNAVAILABLE},
)
def create_city(
    body: CityCreate,
    response: Response,
    conn: Connection = Depends(get_connection),
    cities: CityDAO = Depends(CityDAO),
) -> CityOut:
    """Add a city. A duplicate name answers 409."""
    created = service.create_city(
        conn, cities, NewCity(body.name, body.latitude, body.longitude)
    )
    response.headers["Location"] = f"/v1/cities/{quote(created.name, safe='')}"
    return created
