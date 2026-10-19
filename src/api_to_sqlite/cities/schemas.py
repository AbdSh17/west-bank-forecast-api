"""The JSON shapes of the cities endpoints."""

from pydantic import BaseModel


class CityOut(BaseModel):
    """One city as the API returns it."""

    id: int
    name: str
    latitude: float
    longitude: float


class CityList(BaseModel):
    """The answer of GET /v1/cities: an object with an items array."""

    items: list[CityOut]
