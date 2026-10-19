"""The JSON shapes of the cities endpoints."""

from pydantic import BaseModel, ConfigDict, Field


class CityOut(BaseModel):
    """One city as the API returns it."""

    id: int
    name: str
    latitude: float
    longitude: float


class CityCreate(BaseModel):
    """The JSON body of POST /v1/cities."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class CityList(BaseModel):
    """The answer of GET /v1/cities: an object with an items array."""

    items: list[CityOut]
