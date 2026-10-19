"""Tests for the validation of the POST /v1/cities body. No database is used."""

import pytest
from pydantic import ValidationError

from api_to_sqlite.cities.schemas import CityCreate


def test_a_valid_body_is_accepted():
    city = CityCreate(name="Tulkarm", latitude=32.31, longitude=35.03)
    assert city.name == "Tulkarm"


def test_whitespace_around_the_name_is_removed():
    assert CityCreate(name="  Tulkarm ", latitude=0, longitude=0).name == "Tulkarm"


@pytest.mark.parametrize("name", ["", "   ", "x" * 101])
def test_a_bad_name_is_rejected(name):
    with pytest.raises(ValidationError):
        CityCreate(name=name, latitude=0, longitude=0)


@pytest.mark.parametrize(
    "latitude, longitude", [(90.1, 0), (-90.1, 0), (0, 180.1), (0, -180.1)]
)
def test_coordinates_out_of_range_are_rejected(latitude, longitude):
    with pytest.raises(ValidationError):
        CityCreate(name="Tulkarm", latitude=latitude, longitude=longitude)
